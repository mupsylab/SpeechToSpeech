from __future__ import annotations
import os
import gc
import torch
import torchaudio
from logging import getLogger
logger = getLogger(__name__)
import numpy as np
from time import time as ttime

from BigVGAN.bigvgan import BigVGAN
from transformers import AutoModelForMaskedLM, AutoTokenizer
from AR.models.t2s_lightning_module import Text2SemanticLightningModule
from feature_extractor.cnhubert import CNHubert
from module.models import SynthesizerTrn, SynthesizerTrnV3

from TTS_infer_pack.TextPreprocessor import TextPreprocessor
from TTS_Enitity import TTSRunParam
from TTS_PromptCache import TTS_PromptCache
from TTS_Config import TTS_Config
from TTS_Utils import CutUtil, norm_spec, denorm_spec, mel_fn

class TTS(TTS_PromptCache):
    def _set_seed(self, seed: int):
        import random
        seed = int(seed)
        seed = seed if seed != -1 else random.randrange(1 << 32)
        print(f"Set seed to {seed}")
        os.environ['PYTHONHASHSEED'] = str(seed)
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        try:
            if torch.cuda.is_available():
                torch.cuda.manual_seed(seed)
                torch.cuda.manual_seed_all(seed)
                # torch.backends.cudnn.deterministic = True
                # torch.backends.cudnn.benchmark = False
                # torch.backends.cudnn.enabled = True
                # 开启后会影响精度
                torch.backends.cuda.matmul.allow_tf32 = False
                torch.backends.cudnn.allow_tf32 = False
        except:
            pass
        return seed
    
    def _empty_cache(self):
        try:
            gc.collect()
            if "cuda" in str(self.configs.device):
                torch.cuda.empty_cache()
            elif str(self.configs.device) == "mps":
                torch.mps.empty_cache()
        except:
            pass

    @property
    def precision(self):
        return torch.float16 if self.configs.is_half == True else torch.float32

    def __init__(self, configs: TTS_Config) -> None:
        self.configs = configs
        super().__init__(self)

        self.bert_tokenizer: AutoTokenizer = None
        self.bert_model: AutoModelForMaskedLM = None
        self.cnhuhbert_model: CNHubert = None
        self.t2s_model: Text2SemanticLightningModule = None
        self.vits_model: SynthesizerTrn | SynthesizerTrnV3 = None
        self.bigvgan_model: BigVGAN = None
        self._init_models()

        self.text_preprocessor = TextPreprocessor(self.bert_model, self.bert_tokenizer, self.configs.device)
        self.stop_flag: bool = False

    def _init_models(self):
        self._init_t2s_weights(self.configs.t2s_weights_path)
        self._init_vits_weights(self.configs.vits_weights_path)
        self._init_bert_weights(self.configs.bert_base_path)
        self._init_cnhuhbert_weights(self.configs.cnhuhbert_base_path)
        if self.configs.version == "v3":
            self._init_bigvgan_weights(self.configs.bigvgan_path)

    def _init_bigvgan_weights(self, base_path: str):
        print(f"Loading BigVGAN weights from {base_path}")
        self.bigvgan_model = BigVGAN.from_pretrained(base_path, use_cuda_kernel = False)
        self.bigvgan_model.remove_weight_norm()
        if self.configs.is_half:
            self.bigvgan_model = self.bigvgan_model.half()
        self.bigvgan_model = self.bigvgan_model.to(self.configs.device)
        self.bigvgan_model = self.bigvgan_model.eval()

    def _init_cnhuhbert_weights(self, base_path: str):
        print(f"Loading CNHuBERT weights from {base_path}")
        self.cnhuhbert_model = CNHubert(base_path)
        self.cnhuhbert_model=self.cnhuhbert_model.eval()
        self.cnhuhbert_model = self.cnhuhbert_model.to(self.configs.device)
        if self.configs.is_half and str(self.configs.device)!="cpu":
            self.cnhuhbert_model = self.cnhuhbert_model.half()

    def _init_bert_weights(self, base_path: str):
        print(f"Loading BERT weights from {base_path}")
        self.bert_tokenizer = AutoTokenizer.from_pretrained(base_path)
        self.bert_model = AutoModelForMaskedLM.from_pretrained(base_path)
        self.bert_model=self.bert_model.eval()
        self.bert_model = self.bert_model.to(self.configs.device)
        if self.configs.is_half and str(self.configs.device)!="cpu":
            self.bert_model = self.bert_model.half()

    def _init_vits_weights(self, weights_path: str):
        print(f"Loading VITS weights from {weights_path}")
        self.configs.vits_weights_path = weights_path
        dict_s2 = torch.load(weights_path, map_location=self.configs.device, weights_only=False)
        hps = dict_s2["config"]
        if dict_s2['weight']['enc_p.text_embedding.weight'].shape[0] == 322:
            assert self.configs.version == "v1"
        else:
            assert self.configs.version != "v1"

        hps["model"]["version"] = self.configs.version
        self.configs.filter_length = hps["data"]["filter_length"]
        self.configs.segment_size = hps["train"]["segment_size"]
        self.configs.sampling_rate = hps["data"]["sampling_rate"]
        self.configs.hop_length = hps["data"]["hop_length"]
        self.configs.win_length = hps["data"]["win_length"]
        self.configs.n_speakers = hps["data"]["n_speakers"]
        self.configs.semantic_frame_rate = "25hz"
        kwargs = hps["model"]
        vits_model = SynthesizerTrn(
            self.configs.filter_length // 2 + 1,
            self.configs.segment_size // self.configs.hop_length,
            n_speakers=self.configs.n_speakers,
            **kwargs
        ) if self.configs.version != "v3" else SynthesizerTrnV3(
            self.configs.filter_length // 2 + 1,
            self.configs.segment_size // self.configs.hop_length,
            n_speakers=self.configs.n_speakers,
            **kwargs
        )

        if hasattr(vits_model, "enc_q"):
            del vits_model.enc_q

        vits_model = vits_model.to(self.configs.device)
        vits_model = vits_model.eval()
        vits_model.load_state_dict(dict_s2["weight"], strict=False)
        self.vits_model = vits_model
        if self.configs.is_half and str(self.configs.device)!="cpu":
            self.vits_model = self.vits_model.half()

    def _init_t2s_weights(self, weights_path: str):
        print(f"Loading Text2Semantic weights from {weights_path}")
        self.configs.config.t2s_weights_path = weights_path
        self.configs.hz = 50
        dict_s1 = torch.load(weights_path, map_location=self.configs.device)
        config = dict_s1["config"]
        self.configs.max_sec = config["data"]["max_sec"]
        t2s_model = Text2SemanticLightningModule(config, "****", is_train=False)
        t2s_model.load_state_dict(dict_s1["weight"])
        t2s_model = t2s_model.to(self.configs.device)
        t2s_model = t2s_model.eval()
        self.t2s_model = t2s_model
        if self.configs.is_half and str(self.configs.device)!="cpu":
            self.t2s_model = self.t2s_model.half()

    def set_device(self, device: torch.device, save: bool = True):
        '''
            To set the device for all models.
            Args:
                device: torch.device, the device to use for all models.
        '''
        self.configs.device = device
        if save:
            self.configs.save_config(self.configs)
        if self.t2s_model is not None:
            self.t2s_model = self.t2s_model.to(device)
        if self.vits_model is not None:
            self.vits_model = self.vits_model.to(device)
        if self.bert_model is not None:
            self.bert_model = self.bert_model.to(device)
        if self.cnhuhbert_model is not None:
            self.cnhuhbert_model = self.cnhuhbert_model.to(device)
        if self.bigvgan_model is not None:
            self.bigvgan_model = self.bigvgan_model.to(device)

    def run(self, param: TTSRunParam):
        try:
            for res in self._run_v2(param):
                yield res
        except Exception as e:
            logger.error(e, exc_info=1, stack_info=True)
            yield self.configs.sampling_rate, np.zeros(int(self.configs.sampling_rate), dtype=np.int16)
            del self.t2s_model
            del self.vits_model
            self.t2s_model = None
            self.vits_model = None
            self._init_t2s_weights(self.configs.t2s_weights_path)
            self._init_vits_weights(self.configs.vits_weights_path)
        finally:
            self._empty_cache()

    @torch.no_grad()
    def _run_v2(self, param: TTSRunParam):
        self._set_seed(param.seed)
        zero_wav = torch.zeros(int(self.configs.sampling_rate * 0.2), dtype=self.precision, device=self.configs.device)
        if self.configs.is_half:
            zero_wav = zero_wav.half()


        texts = self.text_preprocessor.pre_seg_text(param.text, param.text_lang, param.text_split_method)
        for i_text, text in enumerate(texts):
            phones1 = self.prompt_cache.phones
            bert1 = self.prompt_cache.bert_features
            phones2, bert2, _ = self.text_preprocessor.segment_and_extract_feature_for_text(text, param.text_lang, self.configs.version)

            bert: torch.Tensor = torch.cat([bert1, bert2], axis = 1)
            all_phones_ids = torch.LongTensor(phones1 + phones2).to(self.configs.device).unsqueeze(0)
            
            bert = bert.to(self.configs.device).unsqueeze(0)
            all_phones_len = torch.tensor([all_phones_ids.shape[-1]]).to(self.configs.device)
            
            pred_semantic, idx = self.t2s_model.model.infer_panel_naive(
                all_phones_ids, all_phones_len, self.prompt_cache.prompt_semantic.unsqueeze(0), bert,
                top_k=param.top_k, top_p=param.top_p, temperature=param.temperature,
                early_stop_num=self.configs.hz * self.configs.max_sec
            )
            pred_semantic = pred_semantic[:, -idx:].unsqueeze(0)

            if self.configs.version != "v3":
                refers = self.prompt_cache.refer_spec[1:] if len(self.prompt_cache.refer_spec) > 1 else self.prompt_cache.refer_spec[0]
                audio = self.vits_model.decode(pred_semantic, torch.LongTensor(phones2).to(self.configs.device).unsqueeze(0), refers, speed=param.speed_factor)[0][0]
            else:
                refer = self.prompt_cache.refer_spec[0]
                fea_ref, ge, mel2, chunk_len, T_min = self.prompt_cache.v3_cache

                phoneme_ids1 = torch.LongTensor(phones2).to(self.configs.device).unsqueeze(0)
                fea_todo, ge = self.vits_model.decode_encp(pred_semantic, phoneme_ids1, refer, ge, param.speed_factor)
                cfm_resss = []
                idx = 0
                while (1):
                    fea_todo_chunk = fea_todo[:, :, idx:idx + chunk_len]
                    if (fea_todo_chunk.shape[-1] == 0): break
                    idx += chunk_len
                    fea = torch.cat([fea_ref, fea_todo_chunk], 2).transpose(2, 1)
                    cfm_res = self.vits_model.cfm.inference(fea, torch.LongTensor([fea.size(1)]).to(fea.device), mel2, 32, inference_cfg_rate=0)
                    cfm_res = cfm_res[:, :, mel2.shape[2]:]
                    mel2 = cfm_res[:, :, -T_min:]
                    fea_ref = fea_todo_chunk[:, :, -T_min:]
                    cfm_resss.append(cfm_res)
                cmf_res = torch.cat(cfm_resss, 2)
                cmf_res = denorm_spec(cmf_res)
                with torch.inference_mode():
                    wav_gen = self.bigvgan_model(cmf_res)
                    audio = wav_gen[0][0]#.cpu().detach().numpy()

            max_audio = torch.abs(audio).max()#简单防止16bit爆音
            if max_audio > 1: audio /= max_audio
            _audio = torch.cat([audio, zero_wav], 0).cpu().detach().numpy()
            yield self.configs.sampling_rate, (_audio * (2 ** 15)).astype(np.int16)
