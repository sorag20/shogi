"""
AlphaZero 用将棋状態クラス（持ち駒対応）

既存の evaluate.py の generate_moves を再利用しつつ:
  - 持ち駒の管理・打ち手生成
  - 駒取り → 手駒に追加
  - 王手判定（全駒種対応版）
  - NN 入力テンソル変換
を追加する。

既存の evaluate.py / train.py は変更せず残す（比較用）。
"""

import numpy as np
from evaluate import (
    initial, generate_moves, inside,
    P, L, N, S, G, B, R, K, PROMOTE,
)

# --------------------------------------------------------------------------
# 定数
# --------------------------------------------------------------------------

# 持ち駒として使える駒種（歩〜飛、成駒は元の種類に戻す）
HAND_TYPES = [P, L, N, S, G, B, R]  # [1,2,3,4,5,6,7]
HAND_IDX   = {p: i for i, p in enumerate(HAND_TYPES)}  # piece → 0..6

# 成駒 → 元の駒種 (例: 9=と → 1=歩)
DEMOTE = {v: k for k, v in PROMOTE.items()}  # {9:1, 10:2, 11:3, 12:4, 13:6, 14:7}

# 各持ち駒の最大枚数（テンソル正規化用）
MAX_HAND = {P: 18, L: 4, N: 4, S: 4, G: 4, B: 2, R: 2}

# NN 入力チャネル数
# ch  0-13 : 先手の駒プレーン（駒種 1-14）
# ch 14-27 : 後手の駒プレーン（駒種 1-14）
# ch 28-34 : 先手の持ち駒 [P,L,N,S,G,B,R] / MAX_HAND（スカラーを面で表現）
# ch 35-41 : 後手の持ち駒 [P,L,N,S,G,B,R] / MAX_HAND
# ch 42    : 手番（先手なら全1、後手なら全0）
INPUT_CHANNELS = 43

# --------------------------------------------------------------------------
# アクション空間のエンコーディング
#
#   盤上の手 : (from_y*9+from_x) * 81 * 2 + (to_y*9+to_x) * 2 + promote
#               → 0 .. 13121  (81*81*2 = 13122 通り)
#   打ち手   : 13122 + piece_idx * 81 + (to_y*9+to_x)
#               → 13122 .. 13688  (7*81 = 567 通り)
# --------------------------------------------------------------------------
_BOARD_MOVE_SIZE = 81 * 81 * 2   # 13122
_DROP_MOVE_SIZE  = len(HAND_TYPES) * 81  # 567
ACTION_SIZE      = _BOARD_MOVE_SIZE + _DROP_MOVE_SIZE  # 13689


def encode_board_move(fy: int, fx: int, ty: int, tx: int, promote: bool) -> int:
    from_pos = fy * 9 + fx
    to_pos   = ty * 9 + tx
    return (from_pos * 81 + to_pos) * 2 + int(promote)


def encode_drop_move(piece_type: int, ty: int, tx: int) -> int:
    pidx   = HAND_IDX[piece_type]
    to_pos = ty * 9 + tx
    return _BOARD_MOVE_SIZE + pidx * 81 + to_pos


def decode_action(action: int):
    """
    Returns:
        ('board', fy, fx, ty, tx, promote)  または
        ('drop',  piece_type, ty, tx)
    """
    if action < _BOARD_MOVE_SIZE:
        promote  = bool(action % 2); action //= 2
        to_pos   = action % 81;      from_pos = action // 81
        return ('board', from_pos // 9, from_pos % 9, to_pos // 9, to_pos % 9, promote)
    else:
        a      = action - _BOARD_MOVE_SIZE
        pidx   = a // 81
        to_pos = a % 81
        return ('drop', HAND_TYPES[pidx], to_pos // 9, to_pos % 9)


# --------------------------------------------------------------------------
# 王手判定（全駒種対応版）
#
# evaluate.py の in_check() は香・桂・成駒を未実装なのでこちらを使う。
# generate_moves(board, -player) で相手の手を全列挙し、
# 玉の位置を攻撃できる手があれば王手と判定する。
# --------------------------------------------------------------------------
def _find_king(board: np.ndarray, player: int):
    target = K * player
    for y in range(9):
        for x in range(9):
            if board[y][x] == target:
                return y, x
    return None


def az_in_check(board: np.ndarray, player: int) -> bool:
    """player の玉が相手に取られうる（王手）なら True"""
    pos = _find_king(board, player)
    if pos is None:
        return True  # 玉が盤上にない = 詰み扱い
    ky, kx = pos
    for _, _, ty, tx, _ in generate_moves(board, -player):
        if ty == ky and tx == kx:
            return True
    return False


# --------------------------------------------------------------------------
# 内部ヘルパー
# --------------------------------------------------------------------------
def _valid_drop_pos(piece_type: int, ty: int, player: int) -> bool:
    """行き所のない駒チェック（盤端への打ち込み禁止）"""
    if player == 1:
        if piece_type == P and ty == 0: return False
        if piece_type == L and ty == 0: return False
        if piece_type == N and ty <= 1: return False
    else:
        if piece_type == P and ty == 8: return False
        if piece_type == L and ty == 8: return False
        if piece_type == N and ty >= 7: return False
    return True


def _has_pawn_in_file(board: np.ndarray, file_x: int, player: int) -> bool:
    """二歩チェック: 指定の筋に同じ手番の歩が既にあるか"""
    pawn = player * P
    for y in range(9):
        if board[y][file_x] == pawn:
            return True
    return False


def _quick_board_play(board: np.ndarray, fy, fx, ty, tx, promote) -> np.ndarray:
    """持ち駒なしの高速盤面適用（az_in_check 内で使用）"""
    nb = board.copy()
    piece = int(nb[fy][fx])
    nb[fy][fx] = 0
    if promote:
        nb[ty][tx] = int(np.sign(piece)) * PROMOTE[abs(piece)]
    else:
        nb[ty][tx] = piece
    return nb


# --------------------------------------------------------------------------
# AZState
# --------------------------------------------------------------------------
class AZState:
    """
    将棋の状態（持ち駒あり）

    Attributes
    ----------
    board  : numpy int8 array shape (9,9)
             正=先手の駒、負=後手の駒、0=空（evaluate.py と同じ符号規則）
    hands  : {1: {P:cnt, L:cnt, ...}, -1: {P:cnt, ...}}
    player : 1(先手) or -1(後手)  ← 手番
    """

    __slots__ = ('board', 'hands', 'player')

    def __init__(self, board=None, hands=None, player: int = 1):
        if board is None:
            self.board = initial.copy().astype(np.int8)
        else:
            self.board = np.asarray(board, dtype=np.int8)

        if hands is None:
            self.hands: dict = {
                 1: {p: 0 for p in HAND_TYPES},
                -1: {p: 0 for p in HAND_TYPES},
            }
        else:
            self.hands = {1: dict(hands[1]), -1: dict(hands[-1])}

        self.player = player

    # ------------------------------------------------------------------
    # 手生成（内部）
    # ------------------------------------------------------------------
    def _gen_board_moves(self):
        """盤上の手を返す。evaluate.py の generate_moves を再利用。"""
        return generate_moves(self.board, self.player)

    def _gen_drop_moves(self):
        """打ち手候補を (piece_type, ty, tx) のリストで返す。"""
        drops = []
        hand  = self.hands[self.player]
        for pt in HAND_TYPES:
            if hand[pt] == 0:
                continue
            for ty in range(9):
                if not _valid_drop_pos(pt, ty, self.player):
                    continue
                for tx in range(9):
                    if self.board[ty][tx] != 0:
                        continue
                    if pt == P and _has_pawn_in_file(self.board, tx, self.player):
                        continue
                    drops.append((pt, ty, tx))
        return drops

    # ------------------------------------------------------------------
    # 手の適用（純粋関数 → 新しい AZState を返す）
    # ------------------------------------------------------------------
    def _apply_board_move(self, fy, fx, ty, tx, promote: bool) -> 'AZState':
        nb    = self.board.copy()
        nh    = {1: dict(self.hands[1]), -1: dict(self.hands[-1])}
        piece = int(nb[fy][fx])
        cap   = int(nb[ty][tx])

        nb[fy][fx] = 0
        if promote:
            nb[ty][tx] = int(np.sign(piece)) * PROMOTE[abs(piece)]
        else:
            nb[ty][tx] = piece

        # 取った駒を手駒に追加（成駒は元の種類に戻す）
        if cap != 0:
            base = DEMOTE.get(abs(cap), abs(cap))
            if base != K:
                nh[self.player][base] += 1

        return AZState(nb, nh, -self.player)

    def _apply_drop_move(self, piece_type: int, ty: int, tx: int) -> 'AZState':
        nb = self.board.copy()
        nh = {1: dict(self.hands[1]), -1: dict(self.hands[-1])}
        nb[ty][tx] = self.player * piece_type
        nh[self.player][piece_type] -= 1
        return AZState(nb, nh, -self.player)

    # ------------------------------------------------------------------
    # 公開 API
    # ------------------------------------------------------------------
    def legal_moves(self) -> list:
        """
        合法手リスト。

        各要素:
            ('board', fy, fx, ty, tx, promote)
            ('drop',  piece_type, ty, tx)
        """
        moves = []

        # ── 盤上の手 ──────────────────────────────────────────────────
        for fy, fx, ty, tx, promote in self._gen_board_moves():
            ns = self._apply_board_move(fy, fx, ty, tx, promote)
            if not az_in_check(ns.board, self.player):
                moves.append(('board', fy, fx, ty, tx, promote))

        # ── 打ち手 ───────────────────────────────────────────────────
        for pt, ty, tx in self._gen_drop_moves():
            ns = self._apply_drop_move(pt, ty, tx)
            if az_in_check(ns.board, self.player):
                continue
            # 打ち歩詰め禁止: 歩を打って相手が詰みになる手は禁手
            if pt == P and az_in_check(ns.board, -self.player):
                # 相手が王手を受けられるか確認（打ち歩詰め判定）
                if _no_legal_moves(ns):
                    continue
            moves.append(('drop', pt, ty, tx))

        return moves

    def play(self, move) -> 'AZState':
        """手を指して新しい AZState を返す。"""
        if move[0] == 'board':
            _, fy, fx, ty, tx, promote = move
            return self._apply_board_move(fy, fx, ty, tx, promote)
        else:
            _, pt, ty, tx = move
            return self._apply_drop_move(pt, ty, tx)

    def is_terminal(self) -> bool:
        """手番プレイヤーに合法手がなければ終局"""
        return len(self.legal_moves()) == 0

    def winner(self):
        """
        終局なら勝利プレイヤー (1 or -1) を返す。
        手番側に合法手なし → 手番側が負け → 相手の勝ち。
        未終局なら None。
        """
        if self.is_terminal():
            return -self.player
        return None

    def encode_move(self, move) -> int:
        """手をアクションインデックスに変換"""
        if move[0] == 'board':
            _, fy, fx, ty, tx, promote = move
            return encode_board_move(fy, fx, ty, tx, promote)
        else:
            _, pt, ty, tx = move
            return encode_drop_move(pt, ty, tx)

    def to_tensor(self) -> np.ndarray:
        """
        NN 入力テンソルに変換。

        Returns
        -------
        ndarray shape (43, 9, 9) float32
        """
        planes = np.zeros((INPUT_CHANNELS, 9, 9), dtype=np.float32)

        # 盤面プレーン
        for y in range(9):
            for x in range(9):
                v = int(self.board[y][x])
                if v > 0:
                    planes[v - 1, y, x] = 1.0          # 先手: ch 0..13
                elif v < 0:
                    planes[14 + (-v - 1), y, x] = 1.0  # 後手: ch 14..27

        # 持ち駒プレーン（各面を count/max で均一に塗りつぶす）
        for i, pt in enumerate(HAND_TYPES):
            black_cnt = self.hands[1][pt]
            white_cnt = self.hands[-1][pt]
            if black_cnt > 0:
                planes[28 + i] = black_cnt / MAX_HAND[pt]
            if white_cnt > 0:
                planes[35 + i] = white_cnt / MAX_HAND[pt]

        # 手番プレーン
        if self.player == 1:
            planes[42] = 1.0

        return planes

    def __repr__(self):
        hand_b = {k: v for k, v in self.hands[1].items() if v > 0}
        hand_w = {k: v for k, v in self.hands[-1].items() if v > 0}
        return (f"AZState(player={self.player}, "
                f"hand_b={hand_b}, hand_w={hand_w})")


# --------------------------------------------------------------------------
# 打ち歩詰め判定用（相手に合法手があるか高速チェック）
# --------------------------------------------------------------------------
def _no_legal_moves(state: AZState) -> bool:
    """
    打ち歩詰め判定専用。
    state.player が合法手を持たないなら True（詰み）。
    高速化のため盤上の手だけ確認し、最初に合法手が見つかり次第 False を返す。
    打ち手も確認するが、そちらは簡易チェックのみ。
    """
    p = state.player
    # 盤上の手を確認
    for fy, fx, ty, tx, promote in generate_moves(state.board, p):
        nb = _quick_board_play(state.board, fy, fx, ty, tx, promote)
        if not az_in_check(nb, p):
            return False
    # 打ち手を確認
    for pt in HAND_TYPES:
        if state.hands[p][pt] == 0:
            continue
        for ty in range(9):
            if not _valid_drop_pos(pt, ty, p):
                continue
            for tx in range(9):
                if state.board[ty][tx] != 0:
                    continue
                if pt == P and _has_pawn_in_file(state.board, tx, p):
                    continue
                nb = state.board.copy()
                nb[ty][tx] = p * pt
                if not az_in_check(nb, p):
                    return False
    return True


# --------------------------------------------------------------------------
# ファクトリ
# --------------------------------------------------------------------------
def initial_state() -> AZState:
    """平手初期局面を返す"""
    return AZState()
