from __future__ import annotations
import torch
import torchaudio
from tools.my_utils import load_audio
from module.mel_processing import spectrogram_torch
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from TTS import TTS

from TTS_Enitity import PromptCache, LanguageV1, LanguageV2

class TTS_PromptCache():
    def __init__(self, runtime: TTS) -> None:
        self.prompt_cache = PromptCache()
        self.configs = runtime.configs
        self.runtime = runtime # 定义运行时，避免类型的循环引用问题

    def _set_ref_audio_path(self, ref_audio_path: str):
        self.prompt_cache.ref_audio_path = ref_audio_path

    def _set_ref_spec(self, ref_audio_path):
        spec = self._get_ref_spec(ref_audio_path)
        if self.prompt_cache.refer_spec in [[], None]:
            self.prompt_cache.refer_spec = [spec]
        else:
            self.prompt_cache.refer_spec[0] = spec

    def _get_ref_spec(self, ref_audio_path):
        audio = load_audio(ref_audio_path, int(self.configs.sampling_rate))
        audio = torch.FloatTensor(audio)
        maxx=audio.abs().max()
        if(maxx>1):audio/=min(2,maxx)
        audio_norm = audio
        audio_norm = audio_norm.unsqueeze(0)
        spec = spectrogram_torch(
            audio_norm,
            self.configs.filter_length,
            self.configs.sampling_rate,
            self.configs.hop_length,
            self.configs.win_length,
            center=False,
        )
        spec = spec.to(self.configs.device)
        if self.configs.is_half:
            spec = spec.half()
        return spec

    def _set_prompt_semantic(self, ref_wav_path:str):
        with torch.no_grad():
            zero_wav_torch = torch.zeros(
                int(self.configs.sampling_rate * 0.3),
                dtype=self.runtime.precision
            )
            wav16k, sr = torchaudio.load(ref_wav_path)

            # v3 版本，音频缓存
            transform = torchaudio.transforms.Resample(sr, 24000)
            self.prompt_cache.ref_audio = wav16k.mean(0).unsqueeze(0)
            self.prompt_cache.ref_audio_sr = 24000

            if sr != 16000:
                transform = torchaudio.transforms.Resample(sr, 16000)
                wav16k = transform(wav16k)
            wav16k = wav16k.mean(0).squeeze(0) # 删除第一个维，Channel
            if wav16k.shape[0] / 16000 > 10 or \
                wav16k.shape[0] / 16000 < 3:
                raise OSError("参考音频在3~10秒范围外，请更换！")

            wav16k = wav16k.to(self.configs.device)
            zero_wav_torch = zero_wav_torch.to(self.configs.device)
            if self.configs.is_half:
                wav16k = wav16k.half()
                zero_wav_torch = zero_wav_torch.half()

            wav16k = torch.cat([wav16k, zero_wav_torch])
            hubert_feature = self.runtime.cnhuhbert_model.model(wav16k.unsqueeze(0))[
                "last_hidden_state"
            ].transpose(1, 2)  # .float()
            codes = self.runtime.vits_model.extract_latent(hubert_feature)

            prompt_semantic = codes[0, 0].to(self.configs.device)
            self.prompt_cache.prompt_semantic = prompt_semantic

    def set_ref_audio(self, ref_audio_path: str):
        '''
            To set the reference audio for the TTS model,
                including the prompt_semantic and refer_spepc.
            Args:
                ref_audio_path: str, the path of the reference audio.
        '''
        self._set_prompt_semantic(ref_audio_path)
        self._set_ref_spec(ref_audio_path)
        self._set_ref_audio_path(ref_audio_path)

    def set_prompt_cache(self, ref_audio_path, prompt_text: str, prompt_lang: LanguageV1 | LanguageV2):
        if self.prompt_cache.prompt_text != prompt_text:
            self.set_ref_audio(ref_audio_path)
            self.prompt_cache.prompt_text = prompt_text
            self.prompt_cache.prompt_lang = prompt_lang
            
            phones, bert_features, norm_text = self.runtime.text_preprocessor.segment_and_extract_feature_for_text(prompt_text, prompt_lang, self.configs.version)
            self.prompt_cache.phones = phones
            self.prompt_cache.bert_features = bert_features
            self.prompt_cache.norm_text = norm_text
