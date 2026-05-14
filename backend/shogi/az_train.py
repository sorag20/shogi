"""
AlphaZero 自己対局 + 学習ループ（個人開発スケール）

フロー:
  1. 自己対局で (状態テンソル, MCTSポリシー, 終局結果) を生成
  2. リプレイバッファに蓄積
  3. バッチ学習（ポリシー: クロスエントロピー + バリュー: MSE）
  4. N イテレーションごとにチェックポイント保存

実行例:
    # デフォルト設定
    python az_train.py

    # 設定を JSON 文字列で上書き
    python az_train.py '{"num_iterations": 5, "games_per_iter": 5, "num_simulations": 50}'
"""

import os
import json
import random
import sys
import time
from datetime import datetime
import numpy as np
import torch
import torch.nn.functional as F
from collections import deque
from typing import List, Tuple

from az_state  import AZState, ACTION_SIZE, initial_state, load_opening_states
from az_model  import AZNet, save_model, load_model, MODEL_PATH, CKPT_DIR, model_summary
from az_mcts   import MCTS

# --------------------------------------------------------------------------
# 型エイリアス
# --------------------------------------------------------------------------
Sample = Tuple[np.ndarray, np.ndarray, float]
# (state_tensor (43,9,9),  mcts_policy (ACTION_SIZE,),  game_result float)


# --------------------------------------------------------------------------
# デフォルト設定
# --------------------------------------------------------------------------
DEFAULT_CFG: dict = dict(
    # ── 自己対局 ──────────────────────────────
    num_iterations   = 5,   # 学習イテレーション数 100
    games_per_iter   = 500,    # 1イテレーションあたりの自己対局数
    num_simulations  = 20,   # 1手あたりの MCTS シミュレーション数
    max_moves        = 300,   # 1局の最大手数（超えたら引き分け）
    temp_threshold   = 30,    # この手数以降は temperature=0 (確定的選択)
    # ── 学習 ──────────────────────────────────
    batch_size       = 1,
    epochs_per_iter  = 5,
    lr               = 0.001,
    weight_decay     = 1e-4,
    buffer_size      = 100_000,  # リプレイバッファ最大サイズ
    # ── チェックポイント ─────────────────────
    checkpoint_every = 10,   # N イテレーションごとに保存
    device           = 'mps',
    # ── 開局ファイル ──────────────────────────
    opening_book     = '/Users/yamakigakuto/dev/shogi/backend/storage/opening_sfen/aoba26523.sfen',
)

# --------------------------------------------------------------------------
# リプレイバッファ
# --------------------------------------------------------------------------
class ReplayBuffer:
    """固定サイズの循環バッファ"""

    def __init__(self, max_size: int):
        self._buf: deque = deque(maxlen=max_size)

    def push(self, samples: List[Sample]) -> None:
        self._buf.extend(samples)

    def sample(self, batch_size: int) -> List[Sample]:
        n = min(batch_size, len(self._buf))
        return random.sample(self._buf, n)

    def __len__(self) -> int:
        return len(self._buf)


# --------------------------------------------------------------------------
# 自己対局
# --------------------------------------------------------------------------
def self_play_game(mcts: MCTS, cfg: dict, opening_states: list = None) -> List[Sample]:
    """
    MCTS を使って 1 局自己対局し、学習サンプルのリストを返す。

    Returns
    -------
    List of (state_tensor, mcts_policy, game_result)
    game_result は局面のプレイヤー視点: +1=勝ち, -1=負け, 0=引き分け
    """
    if opening_states:
        opening_idx = random.randrange(len(opening_states))
        state = opening_states[opening_idx]
    else:
        opening_idx = -1
        state = initial_state()
    history: List[Tuple[np.ndarray, np.ndarray, int]] = []
    # history 要素: (tensor, policy, player_at_step)

    t_legal = 0.0   # legal_moves() の累計時間
    t_mcts  = 0.0   # mcts.search() の累計時間

    for move_num in range(cfg['max_moves']):
        # 千日手検出: 同一局面が4回目なら引き分け終局
        if state.history.count(state._hash()) >= 3:
            break

        # 序盤は temperature=1 で多様性、中盤以降は greedy
        temperature = 1.0 if move_num < cfg['temp_threshold'] else 0.0

        _t = time.time()
        legal = state.legal_moves()
        t_legal += time.time() - _t
        if not legal:
            break  # 詰み

        _t = time.time()
        policy, _ = mcts.search(
            state,
            num_simulations = cfg['num_simulations'],
            temperature     = temperature,
            add_noise       = True,
        )
        t_mcts += time.time() - _t

        # ポリシーから手を選択（0 のときは一様分布にフォールバック）
        actions = [state.encode_move(m) for m in legal]
        probs   = np.array([policy[a] for a in actions], dtype=np.float64)
        s = probs.sum()
        if s == 0:
            probs = np.ones(len(probs), dtype=np.float64) / len(probs)
        else:
            probs /= s

        idx  = int(np.random.choice(len(legal), p=probs))
        history.append((state.to_tensor(), policy, state.player))
        state = state.play(legal[idx])

    # 終局結果（先手視点: +1=先手勝, -1=後手勝, 0=引き分け）
    winner = state.winner() if state.winner() is not None else 0

    # 引き分けには小さいペナルティを与えてAIが引き分けを避けるよう誘導する
    # 手数が長いほど（長引いた引き分けほど）ペナルティを強くする
    draw_penalty = -0.05 if winner == 0 else 0.0

    samples: List[Sample] = []
    for tensor, policy, player in history:
        if winner != 0:
            result = float(winner * player)
        else:
            result = draw_penalty  # 引き分けは手番に関わらず小さい負の値
        samples.append((tensor, policy, result))

    timing = {'legal_moves': t_legal, 'mcts': t_mcts}
    return samples, opening_idx, timing, int(winner)


# --------------------------------------------------------------------------
# 学習ステップ
# --------------------------------------------------------------------------
def train_step(
    model:     AZNet,
    optimizer: torch.optim.Optimizer,
    batch:     List[Sample],
    device:    str,
) -> Tuple[float, float]:
    """
    1 バッチの学習を実行。

    Returns
    -------
    (policy_loss, value_loss)  どちらも float
    """
    tensors, policies, values = zip(*batch)

    x     = torch.tensor(np.array(tensors),  dtype=torch.float32).to(device)
    p_tgt = torch.tensor(np.array(policies), dtype=torch.float32).to(device)
    v_tgt = torch.tensor(np.array(values, dtype=np.float32),
                         dtype=torch.float32).unsqueeze(1).to(device)

    model.train()
    with torch.enable_grad():
        p_logits, v_pred = model(x)

        # ポリシー損失: -sum(pi_mcts * log pi_model)  (KL に相当)
        log_p  = F.log_softmax(p_logits, dim=1)
        p_loss = -(p_tgt * log_p).sum(dim=1).mean()

        # バリュー損失: MSE
        v_loss = F.mse_loss(v_pred, v_tgt)

        loss = p_loss + v_loss
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    return float(p_loss.item()), float(v_loss.item())


# --------------------------------------------------------------------------
# メイン学習ループ
# --------------------------------------------------------------------------
def train(cfg: dict = None) -> AZNet:
    """
    AlphaZero スタイルの自己対局 + 学習を繰り返す。

    Parameters
    ----------
    cfg : 設定を上書きする辞書。None なら DEFAULT_CFG を使用。
    """
    c      = {**DEFAULT_CFG, **(cfg or {})}
    device = c['device']

    print("=" * 60)
    print("AlphaZero 将棋 学習開始")
    print(f"  イテレーション数  : {c['num_iterations']}")
    print(f"  自己対局数/iter   : {c['games_per_iter']}")
    print(f"  MCTS シム数/手    : {c['num_simulations']}")
    print(f"  デバイス          : {device}")
    print("=" * 60)

    model  = load_model(device=device)
    model_summary(model)

    optimizer = torch.optim.Adam(
        model.parameters(), lr=c['lr'], weight_decay=c['weight_decay']
    )
    buf  = ReplayBuffer(c['buffer_size'])
    mcts = MCTS(model, device=device)

    opening_states = None
    if c.get('opening_book'):
        print(f"  開局ファイル読み込み中: {c['opening_book']}")
        opening_states = load_opening_states(c['opening_book'])
        print(f"  開局局面数: {len(opening_states)}")

    os.makedirs(CKPT_DIR, exist_ok=True)

    train_start = time.time()

    for iteration in range(1, c['num_iterations'] + 1):
        iter_start = time.time()
        print(f"\n{'─'*50}")
        print(f"Iteration {iteration}/{c['num_iterations']}")

        # ── 自己対局フェーズ ──────────────────────────────────────────
        new_samples: List[Sample] = []
        wins = draws = losses = 0
        sum_t_legal = sum_t_mcts = 0.0
        selfplay_start = time.time()

        for g in range(c['games_per_iter']):
            samples, opening_idx, timing, winner = self_play_game(mcts, c, opening_states)
            new_samples.extend(samples)
            sum_t_legal += timing['legal_moves']
            sum_t_mcts  += timing['mcts']
            if   winner > 0: wins   += 1
            elif winner < 0: losses += 1
            else:             draws  += 1
            # 進捗表示
            opening_str = f"開局#{opening_idx}" if opening_idx >= 0 else "初期局面"
            print(f"  対局 {g+1:3d}/{c['games_per_iter']}  {opening_str}  "
                  f"手数={len(samples)}  W/D/L={wins}/{draws}/{losses}", end='\r')

        selfplay_elapsed = time.time() - selfplay_start
        buf.push(new_samples)
        print(f"\n  バッファ: {len(buf)} サンプル")
        print(f"  [時間] 自己対局合計: {selfplay_elapsed:.1f}s"
              f"  └ legal_moves: {sum_t_legal:.1f}s ({100*sum_t_legal/selfplay_elapsed:.0f}%)"
              f"  mcts.search: {sum_t_mcts:.1f}s ({100*sum_t_mcts/selfplay_elapsed:.0f}%)")

        # ── 学習フェーズ ──────────────────────────────────────────────
        if len(buf) < c['batch_size']:
            print("  バッファ不足のためスキップ")
            continue

        train_start_phase = time.time()
        total_p = total_v = 0.0
        for _ in range(c['epochs_per_iter']):
            batch      = buf.sample(c['batch_size'])
            pl, vl     = train_step(model, optimizer, batch, device)
            total_p   += pl
            total_v   += vl

        train_elapsed = time.time() - train_start_phase
        n = c['epochs_per_iter']
        print(f"  学習: policy_loss={total_p/n:.4f}  value_loss={total_v/n:.4f}"
              f"  [{train_elapsed:.1f}s]")

        # ── チェックポイント保存 ──────────────────────────────────────
        if iteration % c['checkpoint_every'] == 0:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            ckpt = os.path.join(CKPT_DIR, f'az_iter{iteration:04d}_{ts}.pth')
            torch.save(model.state_dict(), ckpt)
            print(f"  チェックポイント: {ckpt}")

        iter_elapsed = time.time() - iter_start
        elapsed_total = time.time() - train_start
        remaining = iter_elapsed * (c['num_iterations'] - iteration)
        print(f"  時間: {iter_elapsed:.1f}s / 経過: {elapsed_total/60:.1f}min / 残り約: {remaining/60:.1f}min")

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    final_path = MODEL_PATH.replace('.pth', f'_{ts}.pth')
    save_model(model, path=final_path)
    total_elapsed = time.time() - train_start
    print(f"\n{'='*60}")
    print(f"学習完了: {final_path}")
    print(f"総学習時間: {total_elapsed/60:.1f}min ({total_elapsed:.0f}s)")
    return model


# --------------------------------------------------------------------------
# エントリポイント
# --------------------------------------------------------------------------
if __name__ == '__main__':
    override: dict = {}
    if len(sys.argv) > 1:
        try:
            override = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            print(f"[warning] JSON 解析失敗: {sys.argv[1]}")

    train(override)
