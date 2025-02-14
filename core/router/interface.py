from enum import Enum
from pydantic import BaseModel

class Language(str, Enum):
    auto = "auto"
    zh = "zh"
    en = "en"
    yue = "yue"
    ja = "ja"
    ko = "ko"
    nospeech = "nospeech"

class TTS_Request(BaseModel):
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
    fragment_interval:float = 0.3              # float. to control the interval of the audio fragment.
    seed:int = -1                              # int. random seed for reproducibility.
    media_type:str = "wav"                     # str. media type of the output audio, support "wav", "raw", "ogg", "aac".
    streaming_mode:bool = False                # bool. whether to return a streaming response.
    parallel_infer:bool = True                 # bool.(optional) whether to use parallel inference.
    repetition_penalty:float = 1.35            # float.(optional) repetition penalty for T2S model.          
