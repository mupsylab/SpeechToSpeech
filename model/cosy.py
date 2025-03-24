from __future__ import annotations
import os
import sys
sys.path.append("./model")
import torch
import numpy as np
from typing import Generator
from logging import getLogger
logger = getLogger(__name__)

from model.cosyvoice import CosyVoice2
from model.cosyvoice.utils.file_utils import load_wav

def load():
    return CosyVoice2(os.getenv("COSY_MODEL", 'model_pretrained/CosyVoice2-0.5B'),
                      load_jit=False, load_trt=False, fp16=False)
cosyvoice: CosyVoice2 = load()

def stream_io(tts_text: Generator[str]):
    model_output = inference_instruct(tts_text)
    for item in model_output:
        # 防止爆音
        max_audio = torch.abs(item["tts_speech"]).max()
        if max_audio > 1: item["tts_speech"] /= max_audio
        yield (item["tts_speech"] * (2 ** 15)).numpy().astype(np.int16), cosyvoice.sample_rate

cosyvoice.frontend.generate_spk_info(
    "spk",
    os.getenv("PROMPT_TEXT", "你的能力表现会越接近的话。"),
    load_wav(os.getenv("PROMPT_AUDIO", "model_pretrained/CosyVoice2-0.5B/ssy_short.wav"), 16000)
)
ModelOutput = Generator[dict[str, torch.Tensor], None, None]
def inference_instruct(tts_text: str) -> ModelOutput:
    return cosyvoice.inference_instruct2_by_spk_id(
        tts_text, os.getenv("COSY_INSTRUCT", "用平常的语气说话"), "spk", 
        stream=True, text_frontend=False
    )
