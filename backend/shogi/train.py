"""
将棋評価関数の学習スクリプト
- 学習データ: ランダム自己対局で生成した局面
- 正解ラベル: 駒得評価関数（先手駒合計 - 後手駒合計）
- 損失関数: 二乗和誤差 (MSE)
- 最適化: SGD
"""

import torch
import torch.nn as nn
import numpy as np
import random
import os
from evaluate import Net, tensor, initial, generate_moves, play, inside, HAND_TYPES, MAX_HAND
from az_state import initial_state

# 駒の点数（一般的な将棋ソフトの点数スケール）
PIECE_VALUES = {
    1: 100,   # 歩
    2: 300,   # 香
    3: 400,   # 桂
    4: 600,   # 銀
    5: 700,   # 金
    6: 900,   # 角
    7: 1100,  # 飛
    8: 0,     # 玉（無限大なので除外）
    9: 500,   # と（成歩）
    10: 500,  # 成香
    11: 600,  # 成桂
    12: 600,  # 成銀
    13: 1300, # 馬（成角）
    14: 1500, # 龍（成飛）
}


def piece_value_score(board, sente_hand=None, gote_hand=None):
    """駒得評価関数: 先手有利 → 正, 後手有利 → 負 (点数そのまま)"""
    score = 0.0
    for y in range(9):
        for x in range(9):
            val = board[y][x]
            if val == 0:
                continue
            p = abs(int(val))
            v = PIECE_VALUES.get(p, 0.0)
            score += v if val > 0 else -v
    # 持ち駒の価値も加算
    if sente_hand:
        for pt, cnt in sente_hand.items():
            score += PIECE_VALUES.get(pt, 0.0) * cnt
    if gote_hand:
        for pt, cnt in gote_hand.items():
            score -= PIECE_VALUES.get(pt, 0.0) * cnt
    return score


def az_random_game(max_moves=150):
    """AZState でランダム自己対局し、途中の局面（持ち駒付き）を返す"""
    state = initial_state()
    positions = []
    for _ in range(max_moves):
        legal = state.legal_moves()
        if not legal:
            break
        move = random.choice(legal)
        positions.append(state)
        state = state.play(move)
    return positions


LABEL_SCALE = 10000.0  # 学習時の正規化スケール（推論時に掛け戻す）


def _state_to_feature(state):
    """AZState → (feature_95,) の numpy 配列を返す"""
    sente_hand = state.hands[1]
    gote_hand  = state.hands[-1]
    board_vec  = state.board.flatten().astype(np.float32)
    s_vec = np.array(
        [sente_hand.get(p, 0) / MAX_HAND[p] for p in HAND_TYPES], dtype=np.float32
    )
    g_vec = np.array(
        [gote_hand.get(p, 0) / MAX_HAND[p] for p in HAND_TYPES], dtype=np.float32
    )
    return np.concatenate([board_vec, s_vec, g_vec])


def generate_dataset(num_games=500):
    """学習データ生成（持ち駒付き局面）"""
    X, y = [], []
    for _ in range(num_games):
        for state in az_random_game():
            label = piece_value_score(
                state.board, state.hands[1], state.hands[-1]
            ) / LABEL_SCALE
            X.append(_state_to_feature(state))
            y.append([label])

    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.float32)
    print(f"Dataset: {len(X)} positions")
    return torch.tensor(X), torch.tensor(y)


def train(num_games=500, epochs=20, lr=0.001, batch_size=64):
    """学習メインループ"""
    print("=== 学習データ生成中 ===")
    X, y = generate_dataset(num_games)

    model = Net()
    model.train()

    criterion = nn.MSELoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=lr)

    n = len(X)
    print(f"=== 学習開始 (epochs={epochs}, lr={lr}, batch_size={batch_size}) ===")

    for epoch in range(1, epochs + 1):
        # シャッフル
        perm = torch.randperm(n)
        X, y = X[perm], y[perm]

        total_loss = 0.0
        num_batches = 0

        for i in range(0, n, batch_size):
            xb = X[i:i + batch_size]
            yb = y[i:i + batch_size]

            optimizer.zero_grad()
            pred = model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        avg_loss = total_loss / num_batches
        print(f"Epoch {epoch:3d}/{epochs}  loss={avg_loss:.6f}")

    # 保存
    save_path = os.path.join(os.path.dirname(__file__), 'model.pth')
    torch.save(model.state_dict(), save_path)
    print(f"\n=== 学習完了: {save_path} に保存しました ===")
    return model


def self_play_game(model_fn, max_moves=150, gamma=0.95, epsilon=0.1):
    """
    AZState を使って自己対局を1局行い (局面, TDターゲット) のリストを返す。

    model_fn(board, sente_hand, gote_hand) : 先手視点の評価値(float)を返す関数
    gamma           : 割引率（終盤の手ほど報酬が大きく反映される）
    epsilon         : ε-greedy の探索率（ランダム手の確率）
    """
    state  = initial_state()
    history = []
    result  = 0  # 先手視点の最終結果: +1=先手勝, -1=後手勝, 0=引き分け

    for _ in range(max_moves):
        legal = state.legal_moves()
        if not legal:
            result = -state.player  # 合法手なし = 現プレイヤーの負け（先手視点）
            break

        # ε-greedy
        if random.random() < epsilon:
            move = random.choice(legal)
        else:
            best_m, best_v = None, -float('inf')
            for m in legal:
                ns = state.play(m)
                v = model_fn(ns.board, ns.hands[1], ns.hands[-1]) * state.player
                if v > best_v:
                    best_v, best_m = v, m
            move = best_m

        history.append(state)
        state = state.play(move)

    T = len(history)
    samples = []
    for t, st in enumerate(history):
        discount = gamma ** (T - t - 1)
        target = result * discount
        samples.append((st, float(target)))

    return samples, result


def reinforce_train(
    num_epochs=10,
    games_per_epoch=100,
    lr=0.0001,
    gamma=0.95,
    epsilon_start=0.3,
    epsilon_end=0.05,
    batch_size=64,
):
    """
    TD学習による強化学習。
    教師あり学習済みの model.pth を出発点として、自己対局で追加学習する。

    num_epochs      : 強化学習のエポック数
    games_per_epoch : 1エポックあたりの自己対局数
    lr              : 学習率（教師あり学習より小さめ推奨）
    gamma           : 割引率
    epsilon_start/end: ε-greedy の探索率（エポックごとに線形減衰）
    """
    from evaluate import Net, tensor, LABEL_SCALE

    model_path = os.path.join(os.path.dirname(__file__), 'model.pth')

    # 教師あり学習済みモデルを出発点にする
    model = Net()
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location='cpu'))
        print("[RL] 教師あり学習済みモデルを読み込みました")
    else:
        print("[RL] Warning: model.pth が見つかりません。ランダム重みから開始します")

    model.train()
    optimizer = torch.optim.SGD(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    # モデルの推論関数（自己対局内で使用）
    def model_fn(board_arr, sente_hand=None, gote_hand=None):
        with torch.no_grad():
            return model(tensor(board_arr, sente_hand, gote_hand)).item() * LABEL_SCALE

    print(f"=== 強化学習開始 (epochs={num_epochs}, games/epoch={games_per_epoch}) ===")

    for epoch in range(1, num_epochs + 1):
        # ε を線形に減衰
        epsilon = epsilon_start + (epsilon_end - epsilon_start) * (epoch - 1) / max(num_epochs - 1, 1)

        all_states, all_targets = [], []
        win = draw = loss = 0

        for _ in range(games_per_epoch):
            samples, result = self_play_game(model_fn, gamma=gamma, epsilon=epsilon)
            for st, target in samples:
                all_states.append(_state_to_feature(st))
                all_targets.append([target])   # ターゲットは [-1, 1] スケール
            if result > 0:
                win += 1
            elif result < 0:
                loss += 1
            else:
                draw += 1

        if not all_states:
            continue

        X = torch.tensor(np.array(all_states))
        # ターゲットは [-1,1] → 教師あり学習と同じく LABEL_SCALE で割らない
        # （モデル出力は raw 値 ≒ 教師あり学習では label/LABEL_SCALE に合わせてある）
        y = torch.tensor(np.array(all_targets, dtype=np.float32))

        # シャッフル
        perm = torch.randperm(len(X))
        X, y = X[perm], y[perm]

        total_loss, num_batches = 0.0, 0
        for i in range(0, len(X), batch_size):
            xb, yb = X[i:i + batch_size], y[i:i + batch_size]
            optimizer.zero_grad()
            pred = model(xb)
            loss_val = criterion(pred, yb)
            loss_val.backward()
            optimizer.step()
            total_loss += loss_val.item()
            num_batches += 1

        avg_loss = total_loss / max(num_batches, 1)
        print(
            f"Epoch {epoch:3d}/{num_epochs}  ε={epsilon:.3f}  "
            f"loss={avg_loss:.6f}  先手 W/D/L={win}/{draw}/{loss}"
        )

    torch.save(model.state_dict(), model_path)
    print(f"\n[RL] 強化学習完了: {model_path} に保存しました")
    return model


if __name__ == '__main__':
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else 'supervised'

    if mode == 'rl':
        # 強化学習のみ
        reinforce_train(num_epochs=10, games_per_epoch=100)
    elif mode == 'all':
        # 教師あり → 強化学習の順で実行
        train(num_games=500, epochs=20, lr=0.001, batch_size=64)
        reinforce_train(num_epochs=10, games_per_epoch=100)
    else:
        # 教師あり学習のみ（デフォルト）
        train(num_games=500, epochs=20, lr=0.001, batch_size=64)
