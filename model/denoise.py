import os
import torch
import numpy as np
from model.frcrn import FRCRN
model = FRCRN(
    os.getenv("FRCRN_MODEL", "model_pretrained/speech_frcrn_ans_cirm_16k"),
    os.getenv("FRCRN_DEVICE", "cuda"),
)

def denoise(arr: np.ndarray | torch.Tensor, sr: int):
    """
    arr: 一维数组
    sr: 采样率
    """
    if isinstance(arr, np.ndarray):
        arr = torch.from_numpy(arr)
    return model.forward(arr, sr)

