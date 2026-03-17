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
from evaluate import Net, tensor, initial, generate_moves, play, inside

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


def piece_value_score(board):
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
    return score


def random_game(max_moves=60):
    """ランダムに手を進め、途中の局面リストを返す"""
    board = initial.copy()
    player = 1
    positions = []

    for _ in range(max_moves):
        moves = generate_moves(board, player)
        if not moves:
            break
        move = random.choice(moves)
        board = play(board, move)
        positions.append((board.copy(), player))
        player = -player

    return positions


LABEL_SCALE = 10000.0  # 学習時の正規化スケール（推論時に掛け戻す）


def generate_dataset(num_games=500):
    """学習データ生成"""
    X, y = [], []
    for _ in range(num_games):
        for board, _ in random_game():
            label = piece_value_score(board) / LABEL_SCALE  # [-1, 1]付近に正規化
            X.append(board.flatten().astype(np.float32))
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


if __name__ == '__main__':
    train(num_games=500, epochs=20, lr=0.001, batch_size=64)
