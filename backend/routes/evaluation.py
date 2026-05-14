from flask import Blueprint, request, jsonify
import numpy as np
import sys
import os
from datetime import datetime
import az_state as _az_state_mod
from az_mcts import MCTS

evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/api')

# shogi/ ディレクトリを sys.path に追加（az_model が az_state を直接 import するため）
_SHOGI_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'shogi')
)
if _SHOGI_DIR not in sys.path:
    sys.path.insert(0, _SHOGI_DIR)

# Frontend piece type strings → evaluate.py numeric values
# P=1, L=2, N=3, S=4, G=5, B=6, R=7, K=8
PIECE_MAP = {
    'pawn':   1,  # 歩
    'lance':  2,  # 香
    'knight': 3,  # 桂
    'silver': 4,  # 銀
    'gold':   5,  # 金
    'bishop': 6,  # 角
    'rook':   7,  # 飛
    'king':   8,  # 玉/王
}

# Promoted piece values: と=9, 杏=10, 圭=11, 全=12, 馬=13, 龍=14
PROMOTED_MAP = {
    'pawn':   9,
    'lance':  10,
    'knight': 11,
    'silver': 12,
    'bishop': 13,
    'rook':   14,
}


def board_to_numpy(board_data):
    """Convert frontend board JSON to numpy array used by evaluate.py

    BoardState.board is a 9x9 array of Piece | null
    where Piece = { type, owner, promoted }
    """
    board = board_data.get('board', [])
    arr = np.zeros((9, 9), dtype=np.float32)

    for row_idx, row in enumerate(board):
        for col_idx, piece in enumerate(row):
            if piece is None:
                continue

            piece_type = piece.get('type', '')
            owner = piece.get('owner', '')
            promoted = piece.get('promoted', False)

            if promoted and piece_type in PROMOTED_MAP:
                value = PROMOTED_MAP[piece_type]
            elif piece_type in PIECE_MAP:
                value = PIECE_MAP[piece_type]
            else:
                continue

            # 先手(black) = 正, 後手(white) = 負
            if owner == 'white':
                value = -value

            arr[row_idx][col_idx] = value

    return arr


HAND_VALUES = {
    'pawn': 100, 'lance': 300, 'knight': 400,
    'silver': 600, 'gold': 700, 'bishop': 900, 'rook': 1100,
}

# --------------------------------------------------------------------------
# AZ モデル評価
# --------------------------------------------------------------------------
# az_state.py の定数と同じ値
_AZ_HAND_TYPES  = [1, 2, 3, 4, 5, 6, 7]          # P, L, N, S, G, B, R
_AZ_MAX_HAND    = {1: 18, 2: 4, 3: 4, 4: 4, 5: 4, 6: 2, 7: 2}
_AZ_STR_TO_INT  = {'pawn': 1, 'lance': 2, 'knight': 3,
                   'silver': 4, 'gold': 5, 'bishop': 6, 'rook': 7}

_az_model_cache = None


def _get_az_model():
    global _az_model_cache
    if _az_model_cache is None:
        import az_model as _az_mod
        model_path = os.path.join(_SHOGI_DIR, 'az_model.pth')
        _az_model_cache = _az_mod.load_model(model_path, 'cpu')
        _az_model_cache.eval()
    return _az_model_cache


def _board_data_to_az_tensor(board_data):
    """フロントエンドの board JSON を AZ モデル入力テンソル (46, 9, 9) に変換
    ch  0-13: 先手の駒プレーン
    ch 14-27: 後手の駒プレーン
    ch 28-34: 先手の持ち駒
    ch 35-41: 後手の持ち駒
    ch 42   : 手番
    ch 43-44: 千日手検出（フロントエンドからは履歴不明のため 0 固定）
    ch 45   : 総手数（フロントエンドからは不明のため 0 固定）
    """
    board_arr = board_to_numpy(board_data)
    player    = 1 if board_data.get('turn', 'black') == 'black' else -1
    hands_raw = board_data.get('hands', {})

    hands = {1: {p: 0 for p in _AZ_HAND_TYPES}, -1: {p: 0 for p in _AZ_HAND_TYPES}}
    for piece_str, count in hands_raw.get('black', {}).items():
        pt = _AZ_STR_TO_INT.get(piece_str)
        if pt:
            hands[1][pt] = int(count)
    for piece_str, count in hands_raw.get('white', {}).items():
        pt = _AZ_STR_TO_INT.get(piece_str)
        if pt:
            hands[-1][pt] = int(count)

    planes = np.zeros((46, 9, 9), dtype=np.float32)
    for y in range(9):
        for x in range(9):
            v = int(board_arr[y][x])
            if v > 0:
                planes[v - 1, y, x] = 1.0           # 先手: ch 0..13
            elif v < 0:
                planes[14 + (-v - 1), y, x] = 1.0   # 後手: ch 14..27

    for i, pt in enumerate(_AZ_HAND_TYPES):
        if hands[1][pt] > 0:
            planes[28 + i] = hands[1][pt] / _AZ_MAX_HAND[pt]
        if hands[-1][pt] > 0:
            planes[35 + i] = hands[-1][pt] / _AZ_MAX_HAND[pt]

    if player == 1:
        planes[42] = 1.0
    # ch 43, 44 (千日手): 履歴なしのため 0
    # ch 45 (手数): 不明のため 0

    return planes, player


def _az_evaluate(board_data):
    """AZ モデルで評価値を計算。先手視点 (-1000〜+1000) で返す。"""
    import torch
    tensor, player = _board_data_to_az_tensor(board_data)
    model = _get_az_model()
    with torch.no_grad():
        x = torch.tensor(tensor).unsqueeze(0)
        _, value = model(x)
        v = float(value.item())
    # value は手番プレイヤー視点 → 先手視点に変換
    return round(v * player * 1000)


_AZ_INT_TO_STR = {1: 'pawn', 2: 'lance', 3: 'knight', 4: 'silver', 5: 'gold', 6: 'bishop', 7: 'rook'}


def _az_best_move(board_data, num_simulations: int = 50):
    """PV-MCTS による最善手探索。"""


    board_arr = board_to_numpy(board_data)
    player    = 1 if board_data.get('turn', 'black') == 'black' else -1
    hands_raw = board_data.get('hands', {})

    hands = {1: {p: 0 for p in _AZ_HAND_TYPES}, -1: {p: 0 for p in _AZ_HAND_TYPES}}
    for piece_str, count in hands_raw.get('black', {}).items():
        pt = _AZ_STR_TO_INT.get(piece_str)
        if pt:
            hands[1][pt] = int(count)
    for piece_str, count in hands_raw.get('white', {}).items():
        pt = _AZ_STR_TO_INT.get(piece_str)
        if pt:
            hands[-1][pt] = int(count)

    state = _az_state_mod.AZState(board_arr.astype(np.int8), hands, player)
    if not state.legal_moves():
        return None

    model = _get_az_model()
    mcts  = MCTS(model, device='cpu')
    policy, _ = mcts.search(state, num_simulations, temperature=0.0, add_noise=False)
    moves   = state.legal_moves()
    actions = [state.encode_move(m) for m in moves]
    best_a  = max(actions, key=lambda a: policy[a])
    return moves[actions.index(best_a)]


def hand_score(board_data):
    """持ち駒の評価値（先手プラス、後手マイナス）"""
    hands = board_data.get('hands', {})
    score = 0
    for piece_type, count in hands.get('black', {}).items():
        score += HAND_VALUES.get(piece_type, 0) * int(count)
    for piece_type, count in hands.get('white', {}).items():
        score -= HAND_VALUES.get(piece_type, 0) * int(count)
    return score


@evaluation_bp.route('/evaluate', methods=['POST'])
def evaluate():
    """Get evaluation for a position.
    Request body: { board: ..., model: 'nn' | 'az' }  (model は省略時 'nn')
    """
    try:
        data = request.get_json()

        if not data or 'board' not in data:
            return jsonify({'error': 'Bad Request', 'message': 'board is required'}), 400

        board_data = data['board']
        model_type = data.get('model', 'nn')

        if model_type == 'az':
            score = _az_evaluate(board_data)
        else:
            board_arr  = board_to_numpy(board_data)
            hands_raw  = board_data.get('hands', {})
            sente_hand = {_AZ_STR_TO_INT[k]: int(v)
                          for k, v in hands_raw.get('black', {}).items()
                          if k in _AZ_STR_TO_INT}
            gote_hand  = {_AZ_STR_TO_INT[k]: int(v)
                          for k, v in hands_raw.get('white', {}).items()
                          if k in _AZ_STR_TO_INT}
            from shogi.evaluate import evaluate as eval_fn
            score = round(eval_fn(board_arr, sente_hand or None, gote_hand or None))

        return jsonify({
            'evaluation': score,
            'model': model_type,
            'computed_at': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500


PIECE_NAMES_JP = {
    1: '歩', 2: '香', 3: '桂', 4: '銀', 5: '金', 6: '角', 7: '飛', 8: '玉',
    9: 'と', 10: '成香', 11: '成桂', 12: '成銀', 13: '馬', 14: '龍'
}
ROW_KANJI = ['一', '二', '三', '四', '五', '六', '七', '八', '九']


@evaluation_bp.route('/best-move', methods=['POST'])
def best_move_endpoint():
    """現局面の最善手を返す
    Request body: { board: ..., model: 'nn' | 'az' }  (model は省略時 'nn')
    Response: { best_move: notation | null, move_data: { type, ... } | null }
    """
    try:
        data = request.get_json()
        if not data or 'board' not in data:
            return jsonify({'error': 'Bad Request', 'message': 'board is required'}), 400

        board_data  = data['board']
        turn        = board_data.get('turn', 'black')
        player      = 1 if turn == 'black' else -1
        model_type  = data.get('model', 'nn')
        prefix      = '▲' if turn == 'black' else '△'

        if model_type == 'az':
            move = _az_best_move(board_data)
            if move is None:
                return jsonify({'best_move': None, 'move_data': None}), 200

            if move[0] == 'board':
                _, fy, fx, ty, tx, promote = move
                board_arr  = board_to_numpy(board_data)
                piece_val  = int(abs(board_arr[fy][fx]))
                piece_name = PIECE_NAMES_JP.get(piece_val, '?')
                notation   = f'{prefix}{9 - tx}{ROW_KANJI[ty]}{piece_name}{"成" if promote else ""}'
                move_data  = {'type': 'board', 'from_row': fy, 'from_col': fx,
                              'to_row': ty, 'to_col': tx, 'promote': bool(promote)}
            else:
                _, pt, ty, tx = move
                piece_name = PIECE_NAMES_JP.get(pt, '?')
                notation   = f'{prefix}{9 - tx}{ROW_KANJI[ty]}{piece_name}打'
                move_data  = {'type': 'drop', 'piece_type': _AZ_INT_TO_STR.get(pt, '?'),
                              'to_row': ty, 'to_col': tx}
        else:
            board_arr = board_to_numpy(board_data)
            from shogi.evaluate import best_move
            move = best_move(board_arr, player)
            if move is None:
                return jsonify({'best_move': None, 'move_data': None}), 200

            y, x, ny, nx, prom = move
            piece_val  = int(abs(board_arr[y][x]))
            piece_name = PIECE_NAMES_JP.get(piece_val, '?')
            notation   = f'{prefix}{9 - nx}{ROW_KANJI[ny]}{piece_name}{"成" if prom else ""}'
            move_data  = {'type': 'board', 'from_row': y, 'from_col': x,
                          'to_row': ny, 'to_col': nx, 'promote': bool(prom)}

        return jsonify({'best_move': notation, 'move_data': move_data}), 200

    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500


@evaluation_bp.route('/ai-status', methods=['GET'])
def ai_status():
    try:
        from shogi.evaluate import evaluate as eval_fn
        return jsonify({'status': 'healthy'}), 200
    except Exception as e:
        return jsonify({'status': 'unavailable', 'message': str(e)}), 503
