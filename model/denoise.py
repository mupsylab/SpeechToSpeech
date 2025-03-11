import numpy as np
from modelscope.utils.audio.audio_utils import audio_norm
from model.frcrn import FRCRN
model = FRCRN("model_pretrained/speech_frcrn_ans_cirm_16k", "cuda")

def denoise(arr: np.ndarray, sr: int):
    """
    arr: 一维数组
    sr: 采样率
    """
    noise, voice = model.forward(arr, sr)
    return noise, voice

