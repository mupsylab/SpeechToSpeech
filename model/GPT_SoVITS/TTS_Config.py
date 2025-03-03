import os
import yaml
from typing import Dict

from TTS_Enitity import TTSParam

# 模型配置
class TTS_Config:
    CONFIG_PATH = "model_pretrained/GPT_SoVITS/tts_infer.yaml"
    DEFAULT_CONFIG: Dict[str, TTSParam] = {
        "default": TTSParam(),
        "default_v2": TTSParam(version="v2", t2s_weights_path="model_pretrained/GPT_SoVITS/gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt", vits_weights_path="model_pretrained/GPT_SoVITS/gsv-v2final-pretrained/s2G2333k.pth"),
        "default_v3": TTSParam(version="v3", t2s_weights_path="model_pretrained/GPT_SoVITS/s1v3.ckpt", vits_weights_path="model_pretrained/GPT_SoVITS/s2Gv3.pth", bigvgan_path="model_pretrained/GPT_SoVITS/models--nvidia--bigvgan_v2_24khz_100band_256x"),
    }
    def __init__(self, config_path: str = None) -> None:
        if config_path is not None:
            TTS_Config.CONFIG_PATH = config_path
        if not os.path.exists(TTS_Config.CONFIG_PATH):
            self.save_config()
        self.config = self.load_config()
        self.update_config()
        self.max_sec = None
        self.hz:int = 50
        self.semantic_frame_rate:str = "25hz"
        self.segment_size:int = 20480
        self.filter_length:int = 2048
        self.sampling_rate:int = 32000
        self.hop_length:int = 640
        self.win_length:int = 2048
        self.n_speakers:int = 300

    def update_config(self):
        self.device = self.config.device
        self.is_half = self.config.is_half
        self.version = self.config.version
        self.t2s_weights_path = self.config.t2s_weights_path
        self.vits_weights_path = self.config.vits_weights_path
        self.bert_base_path = self.config.bert_base_path
        self.cnhuhbert_base_path = self.config.cnhuhbert_base_path
        self.bigvgan_path = self.config.bigvgan_path

    @classmethod
    def save_config(cls, param: TTSParam = None):
        obj = dict()
        for key, val in cls.DEFAULT_CONFIG.items():
            obj[key] = val.model_dump()
        if param is None:
            # 如果当前设置为空, 则保存默认
            obj["profile"] = "default"
        else:
            obj["profile"] = "custom"
            obj["custom"] = param.model_dump()
        
        with open(cls.CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(obj, f)

    @classmethod
    def load_config(cls):
        with open(cls.CONFIG_PATH, "r") as f:
            configs: dict = yaml.load(f, Loader = yaml.FullLoader)
        profile = configs.get("profile", "default")
        return TTSParam.model_validate(configs[profile], strict=False)
