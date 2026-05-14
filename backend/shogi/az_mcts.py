"""
MCTS（モンテカルロ木探索）with PUCT

AlphaZero 方式:
  - 葉ノードでニューラルネットを呼び出して方策確率とバリューを取得
  - PUCT スコアで子ノードを選択
  - ルートには Dirichlet ノイズを加えて探索多様性を確保
  - 訪問回数から温度付きポリシー分布を生成

最適化:
  - 遅延子状態生成: 子ノードの局面は実際に選択されるまで計算しない

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
EVAL_BATCH_SIZE  = 8     # 1 回の NN フォワードパスで評価する葉ノード数
VIRTUAL_LOSS     = 3     # Select 中に仮加算する仮想損失


# --------------------------------------------------------------------------
# MCTSNode
# --------------------------------------------------------------------------
class MCTSNode:
    """MCTS の 1 ノード（子の局面は遅延生成）"""

    __slots__ = ('state', 'parent', 'move', 'children',
                 'N', 'W', 'Q', 'prior', 'is_expanded', 'vl', '_vl_path')

    def __init__(self,
                 state:  Optional[AZState],
                 parent: Optional['MCTSNode'] = None,
                 move=None,
                 prior: float = 0.0):
        self.state       = state   # None のときは親から遅延計算
        self.parent      = parent
        self.move        = move
        self.children: dict[int, 'MCTSNode'] = {}
        self.N           = 0
        self.W           = 0.0
        self.Q           = 0.0
        self.prior       = prior
        self.is_expanded = False
        self.vl          = 0    # 現在付加されているVirtual Loss合計
        self._vl_path    = []   # このノードへのSelect時に通過したノードリスト

    def ensure_state(self) -> None:
        """state が None なら親の局面から生成する"""
        if self.state is None:
            self.state = self.parent.state.play(self.move)

    def puct_score(self, sqrt_parent_n: float) -> float:
        """PUCT = Q + c_puct * P * sqrt(N_parent) / (1 + N_self)
        N と W には Virtual Loss が既に反映されているため Q を再計算する"""
        q = self.W / self.N if self.N > 0 else 0.0
        return q + C_PUCT * self.prior * sqrt_parent_n / (1.0 + self.N)

    def apply_virtual_loss(self) -> None:
        self.vl += VIRTUAL_LOSS
        self.N  += VIRTUAL_LOSS
        self.W  -= VIRTUAL_LOSS

    def undo_virtual_loss(self) -> None:
        self.vl -= VIRTUAL_LOSS
        self.N  -= VIRTUAL_LOSS
        self.W  += VIRTUAL_LOSS

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
    def _evaluate_batch(self, states: list):
        """複数局面を 1 回のフォワードパスで評価。
        Returns: policies ndarray (N, ACTION_SIZE), values list[float]
        """
        self.model.eval()
        tensors  = np.stack([s.to_tensor() for s in states])
        t        = torch.tensor(tensors, dtype=torch.float32).to(self.device)
        logits, values = self.model(t)
        policies = torch.softmax(logits, dim=1).cpu().numpy()
        values   = values.squeeze(1).cpu().numpy().tolist()
        return policies, values

    def _select(self, node: MCTSNode) -> MCTSNode:
        """展開済みノードを PUCT で下り、葉ノードに到達する。
        通過したノードに Virtual Loss を付加し、他の Select が別パスを選ぶよう誘導する。"""
        path = []
        while node.is_expanded and node.children:
            node = node.best_child()
            node.ensure_state()  # 遅延生成
            node.apply_virtual_loss()
            path.append(node)
        node._vl_path = path  # Backup 時に解除するため一時保存
        return node

    def _expand(self, node: MCTSNode, policy: np.ndarray) -> None:
        """子ノードを作成（局面は遅延生成）"""
        moves = node.state.legal_moves()
        for move in moves:
            action = node.state.encode_move(move)
            child  = MCTSNode(
                state  = None,   # 実際に選択されたときに生成
                parent = node,
                move   = move,
                prior  = float(policy[action]),
            )
            node.children[action] = child
        node.is_expanded = True

    def _backup(self, node: MCTSNode, value: float) -> None:
        """バリューを根まで伝播。手番が変わるたびに符号反転。
        事前に付加した Virtual Loss を解除してから本来の value を加算する。"""
        for vl_node in getattr(node, '_vl_path', []):
            vl_node.undo_virtual_loss()
        node._vl_path = []

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

        Returns
        -------
        policy : ndarray (ACTION_SIZE,)
        value  : float  ルートのバリュー推定（現プレイヤー視点）
        """
        root = MCTSNode(state)

        # ── ルートの初期評価 ─────────────────────────────────────────────
        (root_policy,), (root_value,) = self._evaluate_batch([state])
        if add_noise:
            root_policy = _add_dirichlet_noise(root_policy, state)
        self._expand(root, root_policy)

        if not root.children:
            return np.zeros(ACTION_SIZE, dtype=np.float32), -1.0

        # ── シミュレーションループ（バッチ NN 評価）────────────────────
        sims_done = 0
        while sims_done < num_simulations:
            batch_n = min(EVAL_BATCH_SIZE, num_simulations - sims_done)

            # 選択フェーズ: batch_n 個の葉を収集
            leaves = [self._select(root) for _ in range(batch_n)]
            sims_done += batch_n

            # 終局・展開済みは即バックアップ
            to_eval = []
            for leaf in leaves:
                if leaf.state.is_terminal() or leaf.is_expanded:
                    self._backup(leaf, -1.0)
                else:
                    to_eval.append(leaf)

            if not to_eval:
                continue

            # バッチ NN 評価
            policies, values = self._evaluate_batch([l.state for l in to_eval])

            for leaf, policy, value in zip(to_eval, policies, values):
                if not leaf.is_expanded:
                    self._expand(leaf, policy)
                    self._backup(leaf, float(value))

        return _visits_to_policy(root, temperature), root_value

    def best_move(self, state: AZState, num_simulations: int = 200):
        """最善手を返す（MCTS 使用）"""
        policy, _ = self.search(state, num_simulations,
                                temperature=0.0, add_noise=False)
        moves   = state.legal_moves()
        if not moves:
            return None
        actions = [state.encode_move(m) for m in moves]
        best_a  = max(actions, key=lambda a: policy[a])
        return moves[actions.index(best_a)]

    def best_move_nn(self, state: AZState):
        """最善手を返す（NN 直接推論、MCTS なし）"""
        moves = state.legal_moves()
        if not moves:
            return None
        (policy,), _ = self._evaluate_batch([state])
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
