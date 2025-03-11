import os
import numpy as np
from model.frcrn import FRCRN
model = FRCRN(
    os.getenv("FRCRN_MODEL", "model_pretrained/speech_frcrn_ans_cirm_16k"),
    os.getenv("FRCRN_DEVICE", "cuda"),
)

def denoise(arr: np.ndarray, sr: int):
    """
    arr: 一维数组
    sr: 采样率
    """
    return model.forward(arr, sr)

