"""
model.pth (Net: greedy評価) vs az_model.pth (AZNet: MCTS) 対局 & Elo レーティング算出

使い方:
    python battle.py              # デフォルト: 20局, MCTS 50シム
    python battle.py --games 50 --sims 100
    python battle.py --kifdir ./kifu   # KIF保存先を指定
"""

import argparse
import random
import sys
import numpy as np
import torch
import datetime

from az_state import AZState, initial_state, HAND_TYPES, MAX_HAND
from az_model import AZNet, load_model
from az_mcts import MCTS
from evaluate import Net, HAND_TYPES as EVAL_HAND_TYPES, MAX_HAND as EVAL_MAX_HAND

import os

# ──────────────────────────────────────────────
# KIF 書き出し
# ──────────────────────────────────────────────

_ROW_KANJI = '一二三四五六七八九'

_PIECE_NAME = {
    1: '歩', 2: '香', 3: '桂', 4: '銀', 5: '金', 6: '角', 7: '飛', 8: '玉',
    9: 'と', 10: '成香', 11: '成桂', 12: '成銀', 13: '馬', 14: '龍',
}

_HAND_NAME = {1: '歩', 2: '香', 3: '桂', 4: '銀', 5: '金', 6: '角', 7: '飛'}


def _move_to_kif(move, board_before) -> str:
    """AZState の手タプル → KIF表記文字列"""
    if move[0] == 'board':
        _, fy, fx, ty, tx, promote = move
        piece_id = abs(int(board_before[fy][fx]))
        piece_name = _PIECE_NAME.get(piece_id, '？')
        to_col = 9 - tx          # x=0→9筋, x=8→1筋
        to_row = _ROW_KANJI[ty]  # y=0→一, y=8→九
        from_col = 9 - fx
        from_row = fy + 1
        notation = f'{to_col}{to_row}{piece_name}'
        if promote:
            notation += '成'
        notation += f'({from_col}{from_row})'
    else:
        _, pt, ty, tx = move
        piece_name = _HAND_NAME.get(pt, '？')
        to_col = 9 - tx
        to_row = _ROW_KANJI[ty]
        notation = f'{to_col}{to_row}{piece_name}打'
    return notation


def write_kif(
    path: str,
    sente_name: str,
    gote_name: str,
    move_records,       # list of (move_tuple, board_before_np)
    winner: int,        # 1=先手勝, -1=後手勝, 0=引き分け
    game_index: int,
) -> None:
    """KIF形式で棋譜をファイルに書き出す"""
    now = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')

    if winner == 1:
        result_str = f'まで{len(move_records)}手で先手の勝ち'
        end_note = '後手番投了'
    elif winner == -1:
        result_str = f'まで{len(move_records)}手で後手の勝ち'
        end_note = '先手番投了'
    else:
        result_str = f'まで{len(move_records)}手で引き分け'
        end_note = '引き分け'

    lines = [
        '# ---- KIF形式棋譜ファイル ----',
        f'開始日時：{now}',
        f'棋戦：AI対局 Game {game_index}',
        '手合割：平手',
        f'先手：{sente_name}',
        f'後手：{gote_name}',
        '手数----指し手---------',
    ]

    for i, (move, board_before) in enumerate(move_records):
        move_num = i + 1
        notation = _move_to_kif(move, board_before)
        lines.append(f'{move_num:4d} {notation}')

    total = len(move_records) + 1
    lines.append(f'{total:4d} {end_note}')
    lines.append(result_str)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


# ──────────────────────────────────────────────
# モデル読み込み
# ──────────────────────────────────────────────

def load_net_model():
    """evaluate.py の Net (model.pth) を読み込む"""
    m = Net()
    path = os.path.join(os.path.dirname(__file__), 'model.pth')
    if os.path.exists(path):
        m.load_state_dict(torch.load(path, map_location='mps'))
        print(f"[Net] Loaded: {path}")
    else:
        print(f"[Net] Warning: model.pth not found, using random weights")
    m.eval()
    return m


# ──────────────────────────────────────────────
# プレイヤー定義
# ──────────────────────────────────────────────

def _state_to_tensor_95(state: AZState) -> torch.Tensor:
    """AZState → Net 用の (1, 95) テンソル"""
    board_vec = state.board.flatten().astype(np.float32)
    s_hand = state.hands[1]
    g_hand = state.hands[-1]
    s_vec = np.array(
        [s_hand.get(p, 0) / EVAL_MAX_HAND[p] for p in EVAL_HAND_TYPES],
        dtype=np.float32,
    )
    g_vec = np.array(
        [g_hand.get(p, 0) / EVAL_MAX_HAND[p] for p in EVAL_HAND_TYPES],
        dtype=np.float32,
    )
    t = torch.tensor(np.concatenate([board_vec, s_vec, g_vec]))
    return t.unsqueeze(0)


LABEL_SCALE = 10000.0


class NetPlayer:
    """model.pth を使ったgreedy評価プレイヤー"""

    def __init__(self, model: Net):
        self.model = model
        self.name = "Net(model.pth)"

    def choose_move(self, state: AZState):
        legal = state.legal_moves()
        if not legal:
            return None
        best_m, best_v = None, -float('inf')
        with torch.no_grad():
            for m in legal:
                ns = state.play(m)
                v = self.model(_state_to_tensor_95(ns)).item() * LABEL_SCALE
                v *= state.player  # 現プレイヤー視点に変換
                if v > best_v:
                    best_v, best_m = v, m
        return best_m


class AZPlayer:
    """az_model.pth + MCTS プレイヤー"""

    def __init__(self, model: AZNet, num_simulations: int = 50):
        self.mcts = MCTS(model, device='mps')
        self.num_simulations = num_simulations
        self.name = f"AZNet(az_model.pth, sims={num_simulations})"

    def choose_move(self, state: AZState):
        return self.mcts.best_move(state, self.num_simulations)


# ──────────────────────────────────────────────
# 1局対局
# ──────────────────────────────────────────────

def play_game(sente_player, gote_player, max_moves: int = 300, verbose: bool = False):
    """
    1局対局する。

    Returns
    -------
    winner      : 1 (先手勝), -1 (後手勝), 0 (引き分け)
    move_records: list of (move_tuple, board_before_np)  ← KIF用
    """
    state = initial_state()
    players = {1: sente_player, -1: gote_player}
    move_records = []

    for move_num in range(max_moves):
        if state.is_terminal():
            return -state.player, move_records

        legal = state.legal_moves()
        if not legal:
            return -state.player, move_records

        player = players[state.player]
        move = player.choose_move(state)

        if move is None:
            return -state.player, move_records

        move_records.append((move, state.board.copy()))
        state = state.play(move)

        if verbose and move_num % 20 == 0:
            print(f"  手数 {move_num+1:3d}  手番={'先手' if state.player==-1 else '後手'}", end='\r')

    if verbose:
        print()
    winner = state.winner()
    return (winner if winner is not None else 0), move_records


# ──────────────────────────────────────────────
# Elo 計算
# ──────────────────────────────────────────────

def expected_score(ra: float, rb: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))


def update_elo(ra: float, rb: float, score_a: float, k: float = 32.0):
    """score_a: A の実際のスコア (1=勝, 0.5=引き分け, 0=負け)"""
    ea = expected_score(ra, rb)
    new_ra = ra + k * (score_a - ea)
    new_rb = rb + k * ((1 - score_a) - (1 - ea))
    return new_ra, new_rb


# ──────────────────────────────────────────────
# トーナメント
# ──────────────────────────────────────────────

def run_tournament(num_games: int = 20, num_simulations: int = 50, kif_dir: str = None):
    print("=" * 60)
    print("  model.pth  vs  az_model.pth  対局トーナメント")
    print(f"  総対局数: {num_games}  MCTS シム数: {num_simulations}")
    if kif_dir:
        print(f"  KIF保存先: {kif_dir}")
    print("=" * 60)

    net_model = load_net_model()
    az_model  = load_model(device='mps')

    net_player = NetPlayer(net_model)
    az_player  = AZPlayer(az_model, num_simulations)

    elo_net = 1500.0
    elo_az  = 1500.0

    net_stats = {'win': 0, 'draw': 0, 'loss': 0}
    results = []

    session_ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

    for g in range(1, num_games + 1):
        # 先後を交互に入れ替える
        if g % 2 == 1:
            sente, gote = net_player, az_player
            net_is_sente = True
        else:
            sente, gote = az_player, net_player
            net_is_sente = False

        print(f"\nGame {g:3d}/{num_games}  "
              f"先手={'Net' if net_is_sente else 'AZ '}  "
              f"後手={'AZ ' if net_is_sente else 'Net'}", end='  ')

        winner, move_records = play_game(sente, gote, verbose=False)

        # winner: 1=先手勝, -1=後手勝, 0=引き分け
        if winner == 0:
            net_score = 0.5
            result_str = "引き分け"
            net_stats['draw'] += 1
        elif (winner == 1 and net_is_sente) or (winner == -1 and not net_is_sente):
            net_score = 1.0
            result_str = "Net 勝利"
            net_stats['win'] += 1
        else:
            net_score = 0.0
            result_str = "AZ  勝利"
            net_stats['loss'] += 1

        elo_net, elo_az = update_elo(elo_net, elo_az, net_score)
        results.append(net_score)

        print(f"→ {result_str}  ({len(move_records)}手)  |  Elo: Net={elo_net:.0f}  AZ={elo_az:.0f}")

        # KIF保存
        if kif_dir:
            kif_path = os.path.join(kif_dir, f'{session_ts}_game{g:03d}.kif')
            write_kif(
                path=kif_path,
                sente_name=sente.name,
                gote_name=gote.name,
                move_records=move_records,
                winner=winner,
                game_index=g,
            )
            print(f"  → KIF: {kif_path}")

    # ──────────────────────────────────────────────
    # 最終結果
    # ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  最終結果")
    print("=" * 60)
    print(f"  {net_player.name}")
    print(f"    勝: {net_stats['win']}  引: {net_stats['draw']}  負: {net_stats['loss']}")
    print(f"    勝率: {net_stats['win'] / num_games * 100:.1f}%")
    print(f"    最終 Elo: {elo_net:.1f}")
    print()
    print(f"  {az_player.name}")
    print(f"    勝: {net_stats['loss']}  引: {net_stats['draw']}  負: {net_stats['win']}")
    print(f"    勝率: {net_stats['loss'] / num_games * 100:.1f}%")
    print(f"    最終 Elo: {elo_az:.1f}")
    print()

    diff = elo_az - elo_net
    if abs(diff) < 30:
        verdict = "ほぼ互角"
    elif diff > 0:
        verdict = f"AZNet が {diff:.0f} ポイント上位"
    else:
        verdict = f"Net が {-diff:.0f} ポイント上位"
    print(f"  判定: {verdict}")
    print("=" * 60)

    return elo_net, elo_az


# ──────────────────────────────────────────────
# エントリポイント
# ──────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='model.pth vs az_model.pth Elo tournament')
    parser.add_argument('--games',  type=int,   default=20,      help='総対局数 (default: 20)')
    parser.add_argument('--sims',   type=int,   default=50,      help='AZNet の MCTS シム数 (default: 50)')
    parser.add_argument('--kifdir', type=str,   default='./kifu', help='KIF保存ディレクトリ (default: ./kifu)')
    args = parser.parse_args()

    run_tournament(num_games=args.games, num_simulations=args.sims, kif_dir=args.kifdir)
