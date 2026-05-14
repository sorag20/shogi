"""
AlphaZero 用 ResNet（ポリシー＋バリューヘッド）

個人開発スケール向け設定:
  - フィルタ数: 128  （AlphaZero は 256）
  - 残差ブロック: 6  （AlphaZero は 19 or 39）

入力  : (batch, 46, 9, 9)   ← AZState.to_tensor() の出力
出力  :
  policy : (batch, 13689)    ← softmax 前のロジット
  value  : (batch, 1)        ← tanh 済み [-1, 1]
"""

import os
import torch
import torch.nn as nn
import torch.nn.functional as F

from az_state import INPUT_CHANNELS, ACTION_SIZE

BOARD_SIZE  = 9
NUM_FILTERS = 128   # 個人スケール
NUM_BLOCKS  = 6     # 個人スケール

_MODEL_DIR  = os.path.dirname(__file__)
MODEL_PATH  = os.path.join(_MODEL_DIR, 'az_model.pth')
CKPT_DIR    = os.path.join(_MODEL_DIR, 'az_checkpoints')


# --------------------------------------------------------------------------
# 残差ブロック
# --------------------------------------------------------------------------
class ResBlock(nn.Module):
    """conv3×3 → BN → ReLU → conv3×3 → BN + スキップ接続 → ReLU"""

    def __init__(self, filters: int):
        super().__init__()
        self.conv1 = nn.Conv2d(filters, filters, kernel_size=3, padding=1, bias=False)
        self.bn1   = nn.BatchNorm2d(filters)
        self.conv2 = nn.Conv2d(filters, filters, kernel_size=3, padding=1, bias=False)
        self.bn2   = nn.BatchNorm2d(filters)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        x = F.relu(self.bn1(self.conv1(x)), inplace=True)
        x = self.bn2(self.conv2(x))
        return F.relu(x + residual, inplace=True)


# --------------------------------------------------------------------------
# メインネットワーク
# --------------------------------------------------------------------------
class AZNet(nn.Module):
    """
    Parameters
    ----------
    num_filters : int   残差ブロックのチャネル数（デフォルト 128）
    num_blocks  : int   残差ブロックの数（デフォルト 6）
    """

    def __init__(self, num_filters: int = NUM_FILTERS, num_blocks: int = NUM_BLOCKS):
        super().__init__()

        # ── ステム ──────────────────────────────────────────────────────
        self.stem = nn.Sequential(
            nn.Conv2d(INPUT_CHANNELS, num_filters, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(num_filters),
            nn.ReLU(inplace=True),
        )

        # ── 残差ブロック ────────────────────────────────────────────────
        self.res_blocks = nn.Sequential(
            *[ResBlock(num_filters) for _ in range(num_blocks)]
        )

        # ── ポリシーヘッド ───────────────────────────────────────────────
        self.policy_conv = nn.Sequential(
            nn.Conv2d(num_filters, 2, kernel_size=1, bias=False),
            nn.BatchNorm2d(2),
            nn.ReLU(inplace=True),
            nn.Flatten(),
        )
        self.policy_fc = nn.Linear(2 * BOARD_SIZE * BOARD_SIZE, ACTION_SIZE)

        # ── バリューヘッド ───────────────────────────────────────────────
        self.value_conv = nn.Sequential(
            nn.Conv2d(num_filters, 1, kernel_size=1, bias=False),
            nn.BatchNorm2d(1),
            nn.ReLU(inplace=True),
            nn.Flatten(),
        )
        self.value_fc = nn.Sequential(
            nn.Linear(BOARD_SIZE * BOARD_SIZE, 256),
            nn.ReLU(inplace=True),
            nn.Linear(256, 1),
            nn.Tanh(),
        )

    def forward(self, x: torch.Tensor):
        """
        Returns
        -------
        policy : (batch, ACTION_SIZE)  softmax 前ロジット
        value  : (batch, 1)            tanh [-1, 1]
        """
        x      = self.res_blocks(self.stem(x))
        policy = self.policy_fc(self.policy_conv(x))
        value  = self.value_fc(self.value_conv(x))
        return policy, value


# --------------------------------------------------------------------------
# ユーティリティ
# --------------------------------------------------------------------------
def save_model(model: AZNet, path: str = MODEL_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save(model.state_dict(), path)
    print(f"[AZ] モデル保存: {path}")


def load_model(path: str = MODEL_PATH, device: str = 'cpu') -> AZNet:
    model = AZNet().to(device)
    if os.path.exists(path):
        model.load_state_dict(torch.load(path, map_location=device))
        print(f"[AZ] モデル読み込み: {path}")
    else:
        print(f"[AZ] チェックポイントなし、ランダム重みで開始: {path}")
    return model


def model_summary(model: AZNet) -> None:
    """パラメータ数を表示"""
    n = sum(p.numel() for p in model.parameters())
    print(f"AZNet パラメータ数: {n:,}  ({n/1e6:.2f}M)")
