import { BaseAudioPlayer, StreamAudioPlayer } from "./audio";

interface SensorVoiceResult {
    key: string,
    text: string,
    clean_text: string,
    raw_text: string
}

export function loadBaseAudioFromGPT(s: string, ap: BaseAudioPlayer, url: string) {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", url, true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.responseType = "json";
    xhr.addEventListener("loadend", () => {
        // 数据加载完毕
        const xhr1 = new XMLHttpRequest();
        xhr1.open("GET", `${url}?file_id=${xhr.response.file_id}`, true);
        xhr1.responseType = "arraybuffer";
        xhr1.addEventListener("loadend", () => {
            ap.play(xhr1.response);
        });
        xhr1.send(null);
    });
    xhr.send(JSON.stringify({
        text: s,
        text_lang: "zh",
        ref_audio_path: "output/ssy_的就是，你的能力表现会越接近的话，那你的那个大脑的活动，激活的模式，可能也会越相似。.wav",
        prompt_text: "的就是，你的能力表现会越接近的话，那你的那个大脑的活动，激活的模式，可能也会越相似。",
        prompt_lang: "zh"
    }));
}

export function loadStreamAudioFromGPT(s: string, ap: StreamAudioPlayer, url: string) {
    const text_lang = "zh";
    const ref_audio_path = "output/ssy_的就是，你的能力表现会越接近的话，那你的那个大脑的活动，激活的模式，可能也会越相似。.wav";
    const prompt_lang = "zh";
    const prompt_text = "的就是，你的能力表现会越接近的话，那你的那个大脑的活动，激活的模式，可能也会越相似。";
    const text_split_method = "cut5";
    const batch_size = 2;
    const media_type = "wav";
    const streaming_mode = true;

    fetch(url, {
        method: "POST",
        headers: {
            "Content-type": "application/json"
        },
        body: JSON.stringify({
            text: s,
            text_lang,
            ref_audio_path,
            prompt_lang,
            prompt_text,
            text_split_method,
            batch_size,
            media_type,
            streaming_mode
        })
    })
        .then(r => r.json())
        .then(r => {
            ap.play(`${url}?file_id=${r.file_id}`)
        })
}

export function sttFromSensorVoice(blob: Blob, url: string) {
    return new Promise<SensorVoiceResult[]>((resolve) => {
        const formData = new FormData();
        const audioFile = new File([blob], "asd", { type: "audio/wav" });
        formData.append('files', audioFile);
        formData.append("keys", "asd");
        formData.append("lang", "zh");
        fetch(url, {
            method: "POST",
            body: formData
        }).then(r => r.json())
            .then(r => {
                resolve(r["result"]);
            });
    });
}