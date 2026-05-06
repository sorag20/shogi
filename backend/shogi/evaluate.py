import torch
import torch.nn as nn
import numpy as np
import os

BOARD = 9
# P:歩, L:香, N:桂, S:銀, G:金, B:角, R:飛, K:玉
P,L,N,S,G,B,R,K = 1,2,3,4,5,6,7,8

PROMOTE = {
P:9,L:10,N:11,S:12,B:13,R:14
}

# 持ち駒エンコード用定数
HAND_TYPES = [P, L, N, S, G, B, R]  # [1,2,3,4,5,6,7]
MAX_HAND   = {P: 18, L: 4, N: 4, S: 4, G: 4, B: 2, R: 2}

# 入力: 盤面 81 + 先手持ち駒 7 + 後手持ち駒 7 = 95
_INPUT_SIZE = 95

class Net(nn.Module):

    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(_INPUT_SIZE, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )

    def forward(self,x):
        return self.net(x)

model = Net()
model.eval()

# 学習済み重みがあれば読み込む
_model_path = os.path.join(os.path.dirname(__file__), 'model.pth')
if os.path.exists(_model_path):
    try:
        model.load_state_dict(torch.load(_model_path, map_location='cpu'))
        print(f"[evaluate] Loaded trained model from {_model_path}")
    except Exception as e:
        print(f"[evaluate] Weight load failed ({e}), using random weights")
else:
    print("[evaluate] No trained model found, using random weights")

def tensor(board, sente_hand=None, gote_hand=None):
    """盤面 + 持ち駒を結合して (1, 95) テンソルに変換"""
    board_vec = board.flatten().astype(np.float32)
    s_vec = np.array(
        [(sente_hand.get(p, 0) if sente_hand else 0) / MAX_HAND[p] for p in HAND_TYPES],
        dtype=np.float32,
    )
    g_vec = np.array(
        [(gote_hand.get(p, 0) if gote_hand else 0) / MAX_HAND[p] for p in HAND_TYPES],
        dtype=np.float32,
    )
    t = torch.tensor(np.concatenate([board_vec, s_vec, g_vec]))
    return t.unsqueeze(0)

LABEL_SCALE = 10000.0  # train.py と同じスケール

def evaluate(board, sente_hand=None, gote_hand=None):
    with torch.no_grad():
        return model(tensor(board, sente_hand, gote_hand)).item() * LABEL_SCALE

initial = np.array([
[-2,-3,-4,-5,-8,-5,-4,-3,-2],
[0,-7,0,0,0,0,0,-6,0],
[-1,-1,-1,-1,-1,-1,-1,-1,-1],
[0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0],
[1,1,1,1,1,1,1,1,1],
[0,6,0,0,0,0,0,7,0],
[2,3,4,5,8,5,4,3,2]
])

def inside(y,x):
    return 0<=y<9 and 0<=x<9

king_dirs=[(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
gold_dirs=[(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,0)]
silver_dirs=[(-1,-1),(-1,0),(-1,1),(1,-1),(1,1)]
rook_dirs=[(-1,0),(1,0),(0,-1),(0,1)]
bishop_dirs=[(-1,-1),(-1,1),(1,-1),(1,1)]

def find_king(board,player):
    target = K*player
    for y in range(9):
        for x in range(9):
            if board[y][x]==target:
                return y,x

    return None

def attacks(board,y,x,player):
    p = abs(board[y][x])
    moves=[]
    if p==P:
        moves.append((y-player,x))

    if p==K:
        for dy,dx in king_dirs:
            moves.append((y+dy,x+dx))

    if p==G:
        for dy,dx in gold_dirs:
            moves.append((y+dy*player,x+dx))

    if p==S:
        for dy,dx in silver_dirs:
            moves.append((y+dy*player,x+dx))

    if p==R:
        for dy,dx in rook_dirs:
            for i in range(1,9):
                moves.append((y+dy*i,x+dx*i))

    if p==B:
        for dy,dx in bishop_dirs:
            for i in range(1,9):
                moves.append((y+dy*i,x+dx*i))

    return moves

def in_check(board,player):
    result = find_king(board, player)
    if result is None:
        return True  # 玉が盤上にない = 取られた
    ky, kx = result
    for y in range(9):
        for x in range(9):
            if board[y][x]*player<0:
                for ny,nx in attacks(board,y,x,-player):
                    if inside(ny,nx) and ny==ky and nx==kx:
                        return True

    return False

def promotion_zone(player,y):
    if player==1:
        return y<=2
    else:
        return y>=6

def play(board,move):
    b = board.copy()
    y,x,ny,nx,prom = move
    piece=b[y][x]
    if b[ny][nx]!=0:
        pass

    b[ny][nx]=piece
    b[y][x]=0

    if prom:
        b[ny][nx]=PROMOTE[abs(piece)]*np.sign(piece)

    return b

def _can_prom(p, player, y, ny):
    """移動元または移動先が敵陣なら成れる（成駒・金・玉は不可）"""
    if p not in PROMOTE:
        return False
    return promotion_zone(player, y) or promotion_zone(player, ny)

def _must_prom(p, player, ny):
    """移動先でそれ以上動けない場合は強制成り"""
    if p == P or p == L:
        return (player == 1 and ny == 0) or (player == -1 and ny == 8)
    if p == N:
        return (player == 1 and ny <= 1) or (player == -1 and ny >= 7)
    return False

def _add_step(moves, board, y, x, ny, nx, p, player):
    """1マス移動を候補に追加"""
    if not inside(ny, nx):
        return
    if board[ny][nx] * player > 0:  # 自分の駒
        return
    if _must_prom(p, player, ny):
        moves.append((y, x, ny, nx, True))
    else:
        moves.append((y, x, ny, nx, False))
        if _can_prom(p, player, y, ny):
            moves.append((y, x, ny, nx, True))

def _add_slide(moves, board, y, x, dy, dx, p, player):
    """直進移動を候補に追加（飛・角・香）"""
    ny, nx = y + dy, x + dx
    while inside(ny, nx):
        target = board[ny][nx]
        if target * player > 0:  # 自分の駒
            break
        if _must_prom(p, player, ny):
            moves.append((y, x, ny, nx, True))
        else:
            moves.append((y, x, ny, nx, False))
            if _can_prom(p, player, y, ny):
                moves.append((y, x, ny, nx, True))
        if target != 0:  # 相手の駒を取ったら終了
            break
        ny, nx = ny + dy, nx + dx

# 成駒（と・成香・成桂・成銀）は金と同じ方向
PROMOTED_TO_GOLD = {9, 10, 11, 12}

def generate_moves(board, player):
    moves = []
    for y in range(9):
        for x in range(9):
            piece = board[y][x]
            # 自分の駒かどうかの確認
            if piece * player <= 0:
                continue
            p = abs(piece)

            if p == P:    # 歩：前1マス
                _add_step(moves, board, y, x, y - player, x, p, player)

            elif p == L:  # 香：前直進
                _add_slide(moves, board, y, x, -player, 0, p, player)

            elif p == N:  # 桂：前2+左右1
                _add_step(moves, board, y, x, y - 2*player, x - 1, p, player)
                _add_step(moves, board, y, x, y - 2*player, x + 1, p, player)

            elif p == S:  # 銀：前3方向+斜め後2
                for dy, dx in silver_dirs:
                    _add_step(moves, board, y, x, y + dy*player, x + dx, p, player)

            elif p == G:  # 金：前3+横2+後1
                for dy, dx in gold_dirs:
                    _add_step(moves, board, y, x, y + dy*player, x + dx, p, player)

            elif p == B:  # 角：斜め直進
                for dy, dx in bishop_dirs:
                    _add_slide(moves, board, y, x, dy, dx, p, player)

            elif p == R:  # 飛：縦横直進
                for dy, dx in rook_dirs:
                    _add_slide(moves, board, y, x, dy, dx, p, player)

            elif p == K:  # 玉：全方向1マス
                for dy, dx in king_dirs:
                    _add_step(moves, board, y, x, y + dy, x + dx, p, player)

            elif p in PROMOTED_TO_GOLD:  # と・成香・成桂・成銀 → 金と同じ
                for dy, dx in gold_dirs:
                    _add_step(moves, board, y, x, y + dy*player, x + dx, p, player)

            elif p == 13:  # 馬（成角）：斜め直進+縦横1マス
                for dy, dx in bishop_dirs:
                    _add_slide(moves, board, y, x, dy, dx, p, player)
                for dy, dx in rook_dirs:
                    _add_step(moves, board, y, x, y + dy, x + dx, p, player)

            elif p == 14:  # 竜（成飛）：縦横直進+斜め1マス
                for dy, dx in rook_dirs:
                    _add_slide(moves, board, y, x, dy, dx, p, player)
                for dy, dx in bishop_dirs:
                    _add_step(moves, board, y, x, y + dy, x + dx, p, player)

    return moves

def legal_moves(board,player):
    res=[]
    for m in generate_moves(board,player):
        nb=play(board,m)
        if not in_check(nb,player):
            res.append(m)

    return res

def best_move(board, player):
    best = None
    best_val = -float('inf')
    for m in legal_moves(board, player):
        nb = play(board, m)
        # player=1(先手)は評価値を最大化、player=-1(後手)は最小化→符号反転で統一
        v = evaluate(nb) * player
        if v > best_val:
            best_val = v
            best = m
    return best

if __name__ == '__main__':
    board=initial.copy()
    move=best_move(board,1)
    print("AI move:",move)
