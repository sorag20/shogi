"""
MCTS（モンテカルロ木探索）with PUCT

AlphaZero 方式:
  - 葉ノードでニューラルネットを呼び出して方策確率とバリューを取得
  - PUCT スコアで子ノードを選択
  - ルートには Dirichlet ノイズを加えて探索多様性を確保
  - 訪問回数から温度付きポリシー分布を生成

使い方:
    from az_mcts import MCTS
    from az_model import AZNet

    model = AZNet()
    mcts  = MCTS(model, device='cpu')
    state = initial_state()
    policy, value = mcts.search(state, num_simulations=200)
"""

import math
import numpy as np
import torch
from typing import Optional

from az_state import AZState, ACTION_SIZE

# --------------------------------------------------------------------------
# ハイパーパラメータ
# --------------------------------------------------------------------------
C_PUCT          = 1.5   # 探索・活用のトレードオフ定数
DIRICHLET_ALPHA = 0.3   # Dirichlet ノイズの集中度（将棋: 0.15〜0.3 程度）
DIRICHLET_EPS   = 0.25  # ノイズの混合率


# --------------------------------------------------------------------------
# MCTSNode
# --------------------------------------------------------------------------
class MCTSNode:
    """MCTS の 1 ノード"""

    __slots__ = ('state', 'parent', 'move', 'children',
                 'N', 'W', 'Q', 'prior', 'is_expanded')

    def __init__(self,
                 state:  AZState,
                 parent: Optional['MCTSNode'] = None,
                 move=None,
                 prior: float = 0.0):
        self.state      = state
        self.parent     = parent
        self.move       = move      # 親から辿ったアクション
        self.children: dict[int, 'MCTSNode'] = {}
        self.N          = 0         # 訪問回数
        self.W          = 0.0       # 累積バリュー（自分視点）
        self.Q          = 0.0       # 平均バリュー W/N
        self.prior      = prior     # ポリシーネットの事前確率
        self.is_expanded = False

    def puct_score(self, sqrt_parent_n: float) -> float:
        """PUCT = Q + c_puct * P * sqrt(N_parent) / (1 + N_self)"""
        u = C_PUCT * self.prior * sqrt_parent_n / (1.0 + self.N)
        return self.Q + u

    def best_child(self) -> 'MCTSNode':
        sqrt_n = math.sqrt(self.N) if self.N > 0 else 0.0
        return max(self.children.values(),
                   key=lambda c: c.puct_score(sqrt_n))

    def update(self, value: float) -> None:
        self.N += 1
        self.W += value
        self.Q  = self.W / self.N


# --------------------------------------------------------------------------
# MCTS
# --------------------------------------------------------------------------
class MCTS:
    """
    AlphaZero スタイルの MCTS

    Parameters
    ----------
    model  : AZNet
    device : 'cpu' or 'cuda'
    """

    def __init__(self, model, device: str = 'cpu'):
        self.model  = model
        self.device = device

    @torch.no_grad()
    def _evaluate(self, state: AZState):
        """NN でポリシー確率（numpy, shape ACTION_SIZE）とバリュー（float）を返す"""
        self.model.eval()
        t = torch.tensor(
            state.to_tensor(), dtype=torch.float32
        ).unsqueeze(0).to(self.device)
        logits, value = self.model(t)
        policy = torch.softmax(logits, dim=1).squeeze(0).cpu().numpy()
        return policy, float(value.item())

    def _select(self, node: MCTSNode) -> MCTSNode:
        """展開済みノードを PUCT で下り、葉ノードに到達する"""
        while node.is_expanded and node.children:
            node = node.best_child()
        return node

    def _expand(self, node: MCTSNode, policy: np.ndarray) -> None:
        """ノードを展開して合法手分の子ノードを作成"""
        moves = node.state.legal_moves()
        for move in moves:
            action = node.state.encode_move(move)
            child  = MCTSNode(
                state  = node.state.play(move),
                parent = node,
                move   = move,
                prior  = float(policy[action]),
            )
            node.children[action] = child
        node.is_expanded = True

    def _backup(self, node: MCTSNode, value: float) -> None:
        """バリューを根まで伝播。手番が変わるたびに符号反転。"""
        v = value
        while node is not None:
            node.update(v)
            v    = -v
            node = node.parent

    def search(self,
               state: AZState,
               num_simulations: int = 200,
               temperature: float = 1.0,
               add_noise: bool = True):
        """
        MCTS を num_simulations 回実行し、ポリシー分布とルートバリューを返す。

        Parameters
        ----------
        state           : 探索する局面
        num_simulations : シミュレーション回数
        temperature     : ポリシー分布の温度（0 で最大訪問を選択）
        add_noise       : ルートに Dirichlet ノイズを加えるか（自己対局時 True）

        Returns
        -------
        policy : ndarray (ACTION_SIZE,)  各アクションの選択確率
        value  : float                   ルートのバリュー推定（現プレイヤー視点）
        """
        root = MCTSNode(state)

        # ── ルートの初期評価 ─────────────────────────────────────────────
        root_policy, root_value = self._evaluate(state)
        if add_noise:
            root_policy = _add_dirichlet_noise(root_policy, state)
        self._expand(root, root_policy)

        if not root.children:
            # 合法手なし = 終局
            return np.zeros(ACTION_SIZE, dtype=np.float32), -1.0

        # ── シミュレーションループ ───────────────────────────────────────
        for _ in range(num_simulations):
            leaf = self._select(root)

            if leaf.state.is_terminal():
                # 終局ノード: 手番側が負け
                self._backup(leaf, -1.0)
                continue

            if leaf.is_expanded:
                # すでに展開済み（子なしで is_expanded = 終局）
                self._backup(leaf, -1.0)
                continue

            leaf_policy, leaf_value = self._evaluate(leaf.state)
            self._expand(leaf, leaf_policy)
            self._backup(leaf, leaf_value)

        return _visits_to_policy(root, temperature), root_value

    def best_move(self, state: AZState, num_simulations: int = 200):
        """最善手を返す（評価用）"""
        policy, _ = self.search(state, num_simulations,
                                temperature=0.0, add_noise=False)
        moves   = state.legal_moves()
        if not moves:
            return None
        actions = [state.encode_move(m) for m in moves]
        best_a  = max(actions, key=lambda a: policy[a])
        return moves[actions.index(best_a)]


# --------------------------------------------------------------------------
# ヘルパー
# --------------------------------------------------------------------------
def _add_dirichlet_noise(policy: np.ndarray, state: AZState) -> np.ndarray:
    """ルートのポリシー確率に Dirichlet ノイズを加える"""
    moves = state.legal_moves()
    if not moves:
        return policy
    actions = [state.encode_move(m) for m in moves]
    noise   = np.random.dirichlet([DIRICHLET_ALPHA] * len(actions))
    p       = policy.copy()
    for i, a in enumerate(actions):
        p[a] = (1.0 - DIRICHLET_EPS) * p[a] + DIRICHLET_EPS * noise[i]
    return p


def _visits_to_policy(root: MCTSNode, temperature: float) -> np.ndarray:
    """訪問回数から温度付きポリシー分布を計算"""
    policy  = np.zeros(ACTION_SIZE, dtype=np.float32)
    if not root.children:
        return policy

    actions = list(root.children.keys())
    counts  = np.array([root.children[a].N for a in actions], dtype=np.float64)

    if temperature == 0.0:
        # 最大訪問数の手を確定選択
        best = int(np.argmax(counts))
        policy[actions[best]] = 1.0
    else:
        counts = counts ** (1.0 / temperature)
        total  = counts.sum()
        if total > 0:
            counts /= total
        for a, c in zip(actions, counts):
            policy[a] = float(c)

    return policy
