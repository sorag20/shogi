from flask import Blueprint, request, jsonify
import numpy as np
from datetime import datetime

evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/api')

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
    """Get evaluation for a position using local evaluate.py"""
    try:
        data = request.get_json()

        if not data or 'board' not in data:
            return jsonify({'error': 'Bad Request', 'message': 'board is required'}), 400

        board_data = data['board']
        board_arr = board_to_numpy(board_data)

        from shogi.evaluate import evaluate as eval_fn
        nn_score = eval_fn(board_arr)
        hand_bonus = hand_score(board_data)
        score = round(nn_score) + hand_bonus

        return jsonify({
            'evaluation': score,
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
    """現局面の最善手を返す"""
    try:
        data = request.get_json()
        if not data or 'board' not in data:
            return jsonify({'error': 'Bad Request', 'message': 'board is required'}), 400

        board_data = data['board']
        board_arr = board_to_numpy(board_data)
        turn = board_data.get('turn', 'black')
        player = 1 if turn == 'black' else -1

        from shogi.evaluate import best_move
        move = best_move(board_arr, player)

        if move is None:
            return jsonify({'best_move': None}), 200

        y, x, ny, nx, prom = move
        col_num = 9 - nx
        row_kanji = ROW_KANJI[ny]
        piece_val = int(abs(board_arr[y][x]))
        piece_name = PIECE_NAMES_JP.get(piece_val, '?')
        prefix = '▲' if turn == 'black' else '△'
        notation = f'{prefix}{col_num}{row_kanji}{piece_name}{"成" if prom else ""}'

        return jsonify({'best_move': notation}), 200

    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500


@evaluation_bp.route('/ai-status', methods=['GET'])
def ai_status():
    try:
        from shogi.evaluate import evaluate as eval_fn
        return jsonify({'status': 'healthy'}), 200
    except Exception as e:
        return jsonify({'status': 'unavailable', 'message': str(e)}), 503
