import torch
from typing import Literal
from pydantic import BaseModel, ConfigDict

"""
"all_zh"  #全部按中文识别
"all_ja"  #全部按日文识别
"all_yue" #全部按中文识别
"all_ko"  #全部按韩文识别
"en"      #全部按英文识别#######不变
"zh"      #按中英混合识别####不变
"ja"      #按日英混合识别####不变
"yue"     #按粤英混合识别####不变
"ko"      #按韩英混合识别####不变
"auto_yue"#多语种启动切分识别语种
"auto"    #多语种启动切分识别语种
"""
LanguageV1 = Literal["auto", "en", "zh", "ja",  "all_zh", "all_ja"]
LanguageV2 = Literal["auto", "auto_yue", "en", "zh", "ja", "yue", "ko", "all_zh", "all_ja", "all_yue", "all_ko"]
# 类参数
class TTSParam(BaseModel):
    bert_base_path: str = "model_pretrained/GPT_SoVITS/chinese-roberta-wwm-ext-large"
    cnhuhbert_base_path: str = "model_pretrained/GPT_SoVITS/chinese-hubert-base"
    device: str = "cuda"
    is_half: bool = False
    version: Literal["v1", "v2", "v3"] = "v1"
    t2s_weights_path: str = "model_pretrained/GPT_SoVITS/gsv-v1final-pretrained/s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt"
    vits_weights_path: str = "model_pretrained/GPT_SoVITS/gsv-v1final-pretrained/s2G488k.pth"
    bigvgan_path: str = ""

# 模型启动配置
class TTSRunParam(BaseModel):
    text: str = None                           # str.(required) text to be synthesized
    text_lang: str = None                      # str.(required) language of the text to be synthesized
    ref_audio_path: str = None                 # str.(optional) reference audio path
    aux_ref_audio_paths: list = None           # list.(optional) auxiliary reference audio paths for multi-speaker synthesis
    prompt_lang: str = None                    # str.(optional) prompt text for the reference audio
    prompt_text: str = ""                      # str.(optional) language of the prompt text for the reference audio
    top_k:int = 5                              # int. top k sampling
    top_p:float = 1                            # float. top p sampling
    temperature:float = 1                      # float. temperature for sampling
    text_split_method:str = "cut5"             # str. text split method, see text_segmentation_method.py for details.
    batch_size:int = 1                         # int. batch size for inference
    batch_threshold:float = 0.75               # float. threshold for batch splitting.
    split_bucket:bool = True                   # bool. whether to split the batch into multiple buckets.
    speed_factor:float = 1.0                   # float. control the speed of the synthesized audio.
    return_fragment:bool = False               # bool. step by step return the audio fragment.
    fragment_interval:float = 0.3              # float. to control the interval of the audio fragment.
    seed:int = -1                              # int. random seed for reproducibility.
    parallel_infer:bool = True                 # bool.(optional) whether to use parallel inference.
    repetition_penalty:float = 1.35            # float.(optional) repetition penalty for T2S model.          
    media_type:str = "wav"                     # str. media type of the output audio, support "wav", "raw", "ogg", "aac".
    streaming_mode:bool = False                # bool. whether to return a streaming response.

# 缓存
class PromptCache(BaseModel):
    ref_audio_path: str = None
    ref_audio: torch.Tensor = None
    ref_audio_sr: int = None
    prompt_semantic: torch.Tensor = None
    refer_spec: list[torch.Tensor] = []
    prompt_text: str = None
    prompt_lang: LanguageV1 | LanguageV2 = "audo"
    norm_text: str = None
    phones: list = None
    bert_features: torch.Tensor = None
    aux_ref_audio_paths: list[str] = []

    model_config = ConfigDict(arbitrary_types_allowed=True)
