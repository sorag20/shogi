import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
from az_train import train

if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"

cfg = {
    "num_iterations": 100,
    "games_per_iter": 3,
    "num_simulations": 10,
    "batch_size": 64,
    "epochs_per_iter": 10,
    "device": device,
    "checkpoint_every": 10,
    "max_moves": 100,
}
train(cfg)
