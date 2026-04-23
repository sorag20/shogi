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
import numpy as np
import torch
import torch.nn.functional as F
from collections import deque
from typing import List, Tuple

from az_state  import AZState, ACTION_SIZE, initial_state
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
    num_iterations   = 3,   # 学習イテレーション数 100
    games_per_iter   = 20,    # 1イテレーションあたりの自己対局数
    num_simulations  = 200,   # 1手あたりの MCTS シミュレーション数
    max_moves        = 300,   # 1局の最大手数（超えたら引き分け）
    temp_threshold   = 30,    # この手数以降は temperature=0 (確定的選択)
    # ── 学習 ──────────────────────────────────
    batch_size       = 256,
    epochs_per_iter  = 5,
    lr               = 0.001,
    weight_decay     = 1e-4,
    buffer_size      = 100_000,  # リプレイバッファ最大サイズ
    # ── チェックポイント ─────────────────────
    checkpoint_every = 10,   # N イテレーションごとに保存
    device           = 'cpu',
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
def self_play_game(mcts: MCTS, cfg: dict) -> List[Sample]:
    """
    MCTS を使って 1 局自己対局し、学習サンプルのリストを返す。

    Returns
    -------
    List of (state_tensor, mcts_policy, game_result)
    game_result は局面のプレイヤー視点: +1=勝ち, -1=負け, 0=引き分け
    """
    state    = initial_state()
    history: List[Tuple[np.ndarray, np.ndarray, int]] = []
    # history 要素: (tensor, policy, player_at_step)

    for move_num in range(cfg['max_moves']):
        # 序盤は temperature=1 で多様性、中盤以降は greedy
        temperature = 1.0 if move_num < cfg['temp_threshold'] else 0.0

        legal = state.legal_moves()
        if not legal:
            break  # 詰み

        policy, _ = mcts.search(
            state,
            num_simulations = cfg['num_simulations'],
            temperature     = temperature,
            add_noise       = True,
        )

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

    samples: List[Sample] = []
    for tensor, policy, player in history:
        result = float(winner * player)  # そのプレイヤー視点のバリュー
        samples.append((tensor, policy, result))

    return samples


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

    os.makedirs(CKPT_DIR, exist_ok=True)

    train_start = time.time()

    for iteration in range(1, c['num_iterations'] + 1):
        iter_start = time.time()
        print(f"\n{'─'*50}")
        print(f"Iteration {iteration}/{c['num_iterations']}")

        # ── 自己対局フェーズ ──────────────────────────────────────────
        new_samples: List[Sample] = []
        wins = draws = losses = 0

        for g in range(c['games_per_iter']):
            samples = self_play_game(mcts, c)
            new_samples.extend(samples)
            if samples:
                last_result = samples[-1][2]   # 最終手のプレイヤー視点
                if   last_result > 0: wins   += 1
                elif last_result < 0: losses += 1
                else:                  draws  += 1
            # 進捗表示
            print(f"  対局 {g+1:3d}/{c['games_per_iter']}  "
                  f"手数={len(samples)}  W/D/L={wins}/{draws}/{losses}", end='\r')

        buf.push(new_samples)
        print(f"\n  バッファ: {len(buf)} サンプル")

        # ── 学習フェーズ ──────────────────────────────────────────────
        if len(buf) < c['batch_size']:
            print("  バッファ不足のためスキップ")
            continue

        total_p = total_v = 0.0
        for _ in range(c['epochs_per_iter']):
            batch      = buf.sample(c['batch_size'])
            pl, vl     = train_step(model, optimizer, batch, device)
            total_p   += pl
            total_v   += vl

        n = c['epochs_per_iter']
        print(f"  学習: policy_loss={total_p/n:.4f}  value_loss={total_v/n:.4f}")

        # ── チェックポイント保存 ──────────────────────────────────────
        if iteration % c['checkpoint_every'] == 0:
            ckpt = os.path.join(CKPT_DIR, f'az_iter{iteration:04d}.pth')
            torch.save(model.state_dict(), ckpt)
            print(f"  チェックポイント: {ckpt}")

        iter_elapsed = time.time() - iter_start
        elapsed_total = time.time() - train_start
        remaining = iter_elapsed * (c['num_iterations'] - iteration)
        print(f"  時間: {iter_elapsed:.1f}s / 経過: {elapsed_total/60:.1f}min / 残り約: {remaining/60:.1f}min")

    save_model(model)
    total_elapsed = time.time() - train_start
    print(f"\n{'='*60}")
    print(f"学習完了: {MODEL_PATH}")
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
