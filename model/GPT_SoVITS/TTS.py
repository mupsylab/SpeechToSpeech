from __future__ import annotations
import math
import os
import gc
import torch
from logging import getLogger
logger = getLogger(__name__)
import numpy as np
from time import time as ttime

from transformers import AutoModelForMaskedLM, AutoTokenizer
from AR.models.t2s_lightning_module import Text2SemanticLightningModule
from feature_extractor.cnhubert import CNHubert
from module.models import SynthesizerTrn

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
        self.vits_model: SynthesizerTrn = None
        self._init_models()

        self.text_preprocessor = TextPreprocessor(self.bert_model, self.bert_tokenizer, self.configs.device)
        self.stop_flag: bool = False

    def _init_models(self):
        self._init_t2s_weights(self.configs.t2s_weights_path)
        self._init_vits_weights(self.configs.vits_weights_path)
        self._init_bert_weights(self.configs.bert_base_path)
        self._init_cnhuhbert_weights(self.configs.cnhuhbert_base_path)

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

    def audio_postprocess(self,
                          audio:list[torch.Tensor],
                          sr:int,
                          batch_index_list:list=None,
                          speed_factor:float=1.0,
                          split_bucket:bool=True,
                          fragment_interval:float=0.3
                          )->tuple[int, np.ndarray]:
        zero_wav = torch.zeros(
                        int(self.configs.sampling_rate * fragment_interval),
                        dtype=self.precision,
                        device=self.configs.device
                    )

        for i, batch in enumerate(audio):
            for j, audio_fragment in enumerate(batch):
                max_audio=torch.abs(audio_fragment).max()#简单防止16bit爆音
                if max_audio>1: audio_fragment/=max_audio
                audio_fragment:torch.Tensor = torch.cat([audio_fragment, zero_wav], dim=0)
                audio[i][j] = audio_fragment.cpu().numpy()

        if split_bucket:
            audio = self.recovery_order(audio, batch_index_list)
        else:
            # audio = [item for batch in audio for item in batch]
            audio = sum(audio, [])


        audio = np.concatenate(audio, 0)
        audio = (audio * 32768).astype(np.int16)

        # try:
        #     if speed_factor != 1.0:
        #         audio = speed_change(audio, speed=speed_factor, sr=int(sr))
        # except Exception as e:
        #     print(f"Failed to change speed of audio: \n{e}")

        return sr, audio

    def recovery_order(self, data:list, batch_index_list:list)->list:
        '''
        Recovery the order of the audio according to the batch_index_list.

        Args:
            data (List[list(np.ndarray)]): the out of order audio .
            batch_index_list (List[list[int]]): the batch index list.

        Returns:
            list (List[np.ndarray]): the data in the original order.
        '''
        length = len(sum(batch_index_list, []))
        _data = [None]*length
        for i, index_list in enumerate(batch_index_list):
            for j, index in enumerate(index_list):
                _data[index] = data[i][j]
        return _data

    def to_batch(self, data:list,
                 prompt_data:dict=None,
                 batch_size:int=5,
                 threshold:float=0.75,
                 split_bucket:bool=True,
                 device:torch.device=torch.device("cpu"),
                 precision:torch.dtype=torch.float32,
                 ):
        _data:list = []
        index_and_len_list = []
        for idx, item in enumerate(data):
            norm_text_len = len(item["norm_text"])
            index_and_len_list.append([idx, norm_text_len])

        batch_index_list = []
        if split_bucket:
            index_and_len_list.sort(key=lambda x: x[1])
            index_and_len_list = np.array(index_and_len_list, dtype=np.int64)

            batch_index_list_len = 0
            pos = 0
            while pos <index_and_len_list.shape[0]:
                # batch_index_list.append(index_and_len_list[pos:min(pos+batch_size,len(index_and_len_list))])
                pos_end = min(pos+batch_size,index_and_len_list.shape[0])
                while pos < pos_end:
                    batch=index_and_len_list[pos:pos_end, 1].astype(np.float32)
                    score=batch[(pos_end-pos)//2]/(batch.mean()+1e-8)
                    if (score>=threshold) or (pos_end-pos==1):
                        batch_index=index_and_len_list[pos:pos_end, 0].tolist()
                        batch_index_list_len += len(batch_index)
                        batch_index_list.append(batch_index)
                        pos = pos_end
                        break
                    pos_end=pos_end-1

            assert batch_index_list_len == len(data)

        else:
            for i in range(len(data)):
                if i%batch_size == 0:
                    batch_index_list.append([])
                batch_index_list[-1].append(i)


        for batch_idx, index_list in enumerate(batch_index_list):
            item_list = [data[idx] for idx in index_list]
            phones_list = []
            phones_len_list = []
            # bert_features_list = []
            all_phones_list = []
            all_phones_len_list = []
            all_bert_features_list = []
            norm_text_batch = []
            all_bert_max_len = 0
            all_phones_max_len = 0
            for item in item_list:
                if prompt_data is not None:
                    all_bert_features = torch.cat([prompt_data.bert_features, item["bert_features"]], 1)\
                                                .to(dtype=precision, device=device)
                    all_phones = torch.LongTensor(prompt_data.phones+item["phones"]).to(device)
                    phones = torch.LongTensor(item["phones"]).to(device)
                    # norm_text = prompt_data["norm_text"]+item["norm_text"]
                else:
                    all_bert_features = item["bert_features"]\
                                            .to(dtype=precision, device=device)
                    phones = torch.LongTensor(item["phones"]).to(device)
                    all_phones = phones
                    # norm_text = item["norm_text"]

                all_bert_max_len = max(all_bert_max_len, all_bert_features.shape[-1])
                all_phones_max_len = max(all_phones_max_len, all_phones.shape[-1])

                phones_list.append(phones)
                phones_len_list.append(phones.shape[-1])
                all_phones_list.append(all_phones)
                all_phones_len_list.append(all_phones.shape[-1])
                all_bert_features_list.append(all_bert_features)
                norm_text_batch.append(item["norm_text"])

            phones_batch = phones_list
            all_phones_batch = all_phones_list
            all_bert_features_batch = all_bert_features_list


            max_len = max(all_bert_max_len, all_phones_max_len)
            # phones_batch = self.batch_sequences(phones_list, axis=0, pad_value=0, max_length=max_len)
            #### 直接对phones和bert_features进行pad。（padding策略会影响T2S模型生成的结果，但不直接影响复读概率。影响复读概率的主要因素是mask的策略）
            # all_phones_batch = self.batch_sequences(all_phones_list, axis=0, pad_value=0, max_length=max_len)
            # all_bert_features_batch = all_bert_features_list
            # all_bert_features_batch = torch.zeros((len(all_bert_features_list), 1024, max_len), dtype=precision, device=device)
            # for idx, item in enumerate(all_bert_features_list):
            #     all_bert_features_batch[idx, :, : item.shape[-1]] = item

            # #### 先对phones进行embedding、对bert_features进行project，再pad到相同长度，（padding策略会影响T2S模型生成的结果，但不直接影响复读概率。影响复读概率的主要因素是mask的策略）
            # all_phones_list = [self.t2s_model.model.ar_text_embedding(item.to(self.t2s_model.device)) for item in all_phones_list]
            # all_phones_list = [F.pad(item,(0,0,0,max_len-item.shape[0]),value=0) for item in all_phones_list]
            # all_phones_batch = torch.stack(all_phones_list, dim=0)

            # all_bert_features_list = [self.t2s_model.model.bert_proj(item.to(self.t2s_model.device).transpose(0, 1)) for item in all_bert_features_list]
            # all_bert_features_list = [F.pad(item,(0,0,0,max_len-item.shape[0]), value=0) for item in all_bert_features_list]
            # all_bert_features_batch = torch.stack(all_bert_features_list, dim=0)

            batch = {
                "phones": phones_batch,
                "phones_len": torch.LongTensor(phones_len_list).to(device),
                "all_phones": all_phones_batch,
                "all_phones_len": torch.LongTensor(all_phones_len_list).to(device),
                "all_bert_features": all_bert_features_batch,
                "norm_text": norm_text_batch,
                "max_len": max_len,
            }
            _data.append(batch)

        return _data, batch_index_list

    @torch.no_grad()
    def _run(self, param: TTSRunParam):
        ########## variables initialization ###########
        self.stop_flag:bool = False

        inputs = param.model_dump()
        seed = inputs.get("seed", -1)
        seed = -1 if seed in ["", None] else seed
        self._set_seed(seed)

        text:str = inputs.get("text", "")
        text_lang:str = inputs.get("text_lang", "")
        ref_audio_path:str = inputs.get("ref_audio_path", "")
        aux_ref_audio_paths:list = inputs.get("aux_ref_audio_paths", [])
        prompt_text:str = inputs.get("prompt_text", "")
        prompt_lang:str = inputs.get("prompt_lang", "")
        top_k:int = inputs.get("top_k", 5)
        top_p:float = inputs.get("top_p", 1)
        temperature:float = inputs.get("temperature", 1)
        text_split_method:str = inputs.get("text_split_method", "cut0")
        batch_size = inputs.get("batch_size", 1)
        batch_threshold = inputs.get("batch_threshold", 0.75)
        speed_factor = inputs.get("speed_factor", 1.0)
        split_bucket = inputs.get("split_bucket", True)
        return_fragment = inputs.get("return_fragment", False)
        fragment_interval = inputs.get("fragment_interval", 0.3)
        parallel_infer = inputs.get("parallel_infer", True)
        repetition_penalty = inputs.get("repetition_penalty", 1.35)


        if parallel_infer:
            print("并行推理模式已开启")
            self.t2s_model.model.infer_panel = self.t2s_model.model.infer_panel_batch_infer
        else:
            print("并行推理模式已关闭")
            self.t2s_model.model.infer_panel = self.t2s_model.model.infer_panel_naive_batched

        if return_fragment:
            print("分段返回模式已开启")
            if split_bucket:
                split_bucket = False
                print("分段返回模式不支持分桶处理，已自动关闭分桶处理")

        if split_bucket and speed_factor==1.0:
            print("分桶处理模式已开启")
        elif speed_factor!=1.0:
            print("语速调节不支持分桶处理，已自动关闭分桶处理")
            split_bucket = False
        else:
            print("分桶处理模式已关闭")

        if fragment_interval<0.01:
            fragment_interval = 0.01
            print("分段间隔过小，已自动设置为0.01")

        no_prompt_text = False
        if prompt_text in [None, ""]:
            no_prompt_text = True

        if ref_audio_path in [None, ""] and \
            ((self.prompt_cache.prompt_semantic is None) or (self.prompt_cache.refer_spec in [None, []])):
            raise ValueError("ref_audio_path cannot be empty, when the reference audio is not set using set_ref_audio()")

        ###### setting reference audio and prompt text preprocessing ########
        t0 = ttime()
        if (ref_audio_path is not None) and (ref_audio_path != self.prompt_cache.ref_audio_path):
            if not os.path.exists(ref_audio_path):
                raise ValueError(f"{ref_audio_path} not exists")
            self.set_ref_audio(ref_audio_path)
            
        aux_ref_audio_paths = aux_ref_audio_paths if aux_ref_audio_paths is not None else []
        paths = set(aux_ref_audio_paths)&set(self.prompt_cache.aux_ref_audio_paths)
        if not (len(list(paths)) == len(aux_ref_audio_paths) == len(self.prompt_cache.aux_ref_audio_paths)):
            self.prompt_cache.aux_ref_audio_paths = aux_ref_audio_paths
            self.prompt_cache.refer_spec = [self.prompt_cache.refer_spec[0]]
            for path in aux_ref_audio_paths:
                if path in [None, ""]:
                    continue
                if not os.path.exists(path):
                    print("音频文件不存在，跳过：{}".format(path))
                    continue
                self.prompt_cache.refer_spec.append(self._get_ref_spec(path))
                
        if not no_prompt_text:
            prompt_text = prompt_text.strip("\n")
            if (prompt_text[-1] not in CutUtil.splits): prompt_text += "。" if prompt_lang != "en" else "."
            print("实际输入的参考文本:", prompt_text)
            if self.prompt_cache.prompt_text != prompt_text:
                self.prompt_cache.prompt_text = prompt_text
                self.prompt_cache.prompt_lang = prompt_lang
                phones, bert_features, norm_text = \
                    self.text_preprocessor.segment_and_extract_feature_for_text(
                                                                        prompt_text, 
                                                                        prompt_lang,
                                                                        self.configs.version)
                self.prompt_cache.phones = phones
                self.prompt_cache.bert_features = bert_features
                self.prompt_cache.norm_text = norm_text




        ###### text preprocessing ########
        t1 = ttime()
        data:list = None
        if not return_fragment:
            data = self.text_preprocessor.preprocess(text, text_lang, text_split_method, self.configs.version)
            if len(data) == 0:
                yield self.configs.sampling_rate, np.zeros(int(self.configs.sampling_rate),
                                                            dtype=np.int16)
                return

            batch_index_list:list = None
            data, batch_index_list = self.to_batch(data, 
                                prompt_data=self.prompt_cache if not no_prompt_text else None, 
                                batch_size=batch_size, 
                                threshold=batch_threshold,
                                split_bucket=split_bucket,
                                device=self.configs.device,
                                precision=self.precision
                                )
        else:
            print("############ 切分文本 ############")
            texts = self.text_preprocessor.pre_seg_text(text, text_lang, text_split_method)
            data: list[list[str]] = []
            for i in range(len(texts)):
                if i%batch_size == 0:
                    data.append([])
                data[-1].append(texts[i])
            
            def make_batch(batch_texts):
                batch_data = []
                print("############ 提取文本Bert特征 ############")
                for text in batch_texts:
                    phones, bert_features, norm_text = self.text_preprocessor.segment_and_extract_feature_for_text(text, text_lang, self.configs.version)
                    if phones is None:
                        continue
                    res={
                        "phones": phones,
                        "bert_features": bert_features,
                        "norm_text": norm_text,
                    }
                    batch_data.append(res)
                if len(batch_data) == 0:
                    return None
                batch, _ = self.to_batch(batch_data, 
                            prompt_data=self.prompt_cache if not no_prompt_text else None, 
                            batch_size=batch_size, 
                            threshold=batch_threshold,
                            split_bucket=False,
                            device=self.configs.device,
                            precision=self.precision
                            )
                return batch[0]


        t2 = ttime()
        print("############ 推理 ############")
        ###### inference ######
        t_34 = 0.0
        t_45 = 0.0
        audio = []
        for item in data:
            t3 = ttime()
            if return_fragment:
                item = make_batch(item)
                if item is None:
                    continue

            batch_phones:list[torch.LongTensor] = item["phones"]
            # batch_phones:torch.LongTensor = item["phones"]
            batch_phones_len:torch.LongTensor = item["phones_len"]
            all_phoneme_ids:torch.LongTensor = item["all_phones"]
            all_phoneme_lens:torch.LongTensor  = item["all_phones_len"]
            all_bert_features:torch.LongTensor = item["all_bert_features"]
            norm_text:str = item["norm_text"]
            max_len = item["max_len"]

            if no_prompt_text :
                prompt = None
            else:
                prompt = self.prompt_cache.prompt_semantic.expand(len(all_phoneme_ids), -1).to(self.configs.device)


            pred_semantic_list, idx_list = self.t2s_model.model.infer_panel(
                all_phoneme_ids,
                all_phoneme_lens,
                prompt,
                all_bert_features,
                # prompt_phone_len=ph_offset,
                top_k=top_k,
                top_p=top_p,
                temperature=temperature,
                early_stop_num=self.configs.hz * self.configs.max_sec,
                max_len=max_len,
                repetition_penalty=repetition_penalty,
            )
            t4 = ttime()
            t_34 += t4 - t3

            refer_audio_spec:torch.Tensor = [item.to(dtype=self.precision, device=self.configs.device) for item in self.prompt_cache.refer_spec]
                                                

            batch_audio_fragment = []
        
            # ## vits并行推理 method 1
            # pred_semantic_list = [item[-idx:] for item, idx in zip(pred_semantic_list, idx_list)]
            # pred_semantic_len = torch.LongTensor([item.shape[0] for item in pred_semantic_list]).to(self.configs.device)
            # pred_semantic = self.batch_sequences(pred_semantic_list, axis=0, pad_value=0).unsqueeze(0)
            # max_len = 0
            # for i in range(0, len(batch_phones)):
            #     max_len = max(max_len, batch_phones[i].shape[-1])
            # batch_phones = self.batch_sequences(batch_phones, axis=0, pad_value=0, max_length=max_len)
            # batch_phones = batch_phones.to(self.configs.device)
            # batch_audio_fragment = (self.vits_model.batched_decode(
            #         pred_semantic, pred_semantic_len, batch_phones, batch_phones_len,refer_audio_spec
            #     ))

            if speed_factor == 1.0:
                # ## vits并行推理 method 2
                pred_semantic_list = [item[-idx:] for item, idx in zip(pred_semantic_list, idx_list)]
                upsample_rate = math.prod(self.vits_model.upsample_rates)
                audio_frag_idx = [pred_semantic_list[i].shape[0]*2*upsample_rate for i in range(0, len(pred_semantic_list))]
                audio_frag_end_idx = [ sum(audio_frag_idx[:i+1]) for i in range(0, len(audio_frag_idx))]
                all_pred_semantic = torch.cat(pred_semantic_list).unsqueeze(0).unsqueeze(0).to(self.configs.device)
                _batch_phones = torch.cat(batch_phones).unsqueeze(0).to(self.configs.device)
                _batch_audio_fragment = (self.vits_model.decode(
                        all_pred_semantic, _batch_phones, refer_audio_spec, speed=speed_factor
                    ).detach()[0, 0, :])
                audio_frag_end_idx.insert(0, 0)
                batch_audio_fragment= [_batch_audio_fragment[audio_frag_end_idx[i-1]:audio_frag_end_idx[i]] for i in range(1, len(audio_frag_end_idx))]
            else:
            # ## vits串行推理
                for i, idx in enumerate(idx_list):
                    phones = batch_phones[i].unsqueeze(0).to(self.configs.device)
                    _pred_semantic = (pred_semantic_list[i][-idx:].unsqueeze(0).unsqueeze(0))   # .unsqueeze(0)#mq要多unsqueeze一次
                    audio_fragment =(self.vits_model.decode(
                            _pred_semantic, phones, refer_audio_spec, speed=speed_factor
                        ).detach()[0, 0, :])
                    batch_audio_fragment.append(
                        audio_fragment
                    )  ###试试重建不带上prompt部分

            t5 = ttime()
            t_45 += t5 - t4
            if return_fragment:
                print("%.3f\t%.3f\t%.3f\t%.3f" % (t1 - t0, t2 - t1, t4 - t3, t5 - t4))
                yield self.audio_postprocess([batch_audio_fragment], 
                                                self.configs.sampling_rate, 
                                                None, 
                                                speed_factor, 
                                                False,
                                                fragment_interval
                                                )
            else:
                audio.append(batch_audio_fragment)

            if self.stop_flag:
                yield self.configs.sampling_rate, np.zeros(int(self.configs.sampling_rate), dtype=np.int16)
                return

        if not return_fragment:
            print("%.3f\t%.3f\t%.3f\t%.3f" % (t1 - t0, t2 - t1, t_34, t_45))
            if len(audio) == 0:
                yield self.configs.sampling_rate, np.zeros(int(self.configs.sampling_rate), dtype=np.int16)
            else:
                yield self.audio_postprocess(audio, 
                                             self.configs.sampling_rate, 
                                             batch_index_list, 
                                             speed_factor, 
                                             split_bucket,
                                             fragment_interval
                                             )

    @torch.no_grad()
    def _run_v2(self, param: TTSRunParam):
        self._set_seed(param.seed)
        zero_wav = torch.zeros(int(self.configs.sampling_rate * 0.2), dtype=self.precision, device=self.configs.device)
        if self.configs.is_half:
            zero_wav = zero_wav.half()

        phones1 = self.prompt_cache.phones
        bert1 = self.prompt_cache.bert_features
        norm_text1 = self.prompt_cache.norm_text
        
        texts = self.text_preprocessor.pre_seg_text(param.text, param.text_lang, param.text_split_method)
        for i_text, text in enumerate(texts):
            phones2, bert2, norm_text2 = self.text_preprocessor.segment_and_extract_feature_for_text(text, param.text_lang, self.configs.version)

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

            refers = self.prompt_cache.refer_spec[1:] if len(self.prompt_cache.refer_spec) > 1 else self.prompt_cache.refer_spec[0]
            audio = self.vits_model.decode(pred_semantic, torch.LongTensor(phones2).to(self.configs.device).unsqueeze(0), refers, speed=param.speed_factor)[0][0]

            max_audio = torch.abs(audio).max()#简单防止16bit爆音
            if max_audio > 1: audio /= max_audio
            _audio = torch.cat([audio, zero_wav], 0).cpu().detach().numpy()
            yield self.configs.sampling_rate, (_audio * (2 ** 15)).astype(np.int16)
