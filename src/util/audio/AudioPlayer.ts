interface Audio {
    currAudioArray: Uint8Array;
}
interface AudioPlayer extends Audio {
    status: 'playing' | 'stop';
}
interface AnalyserOption {
    fftSize: number;
    smoothingTimeConstant: number;
    minDecibels: number;
    maxDecibels: number;
};
export class BaseAudioPlayer implements AudioPlayer {
    private audioContext: AudioContext | null = null;
    private source: AudioBufferSourceNode | null = null;
    private analyser: AnalyserNode | null = null;
    private options: AnalyserOption;

    private isPlaying: boolean = false;
    constructor(options?: Partial<AnalyserOption>) {
        this.options = {
            minDecibels: -90,
            maxDecibels: -10,
            smoothingTimeConstant: 0.8,
            fftSize: 256,
            ...options
        }
        this.validateOptions();
    }
    private validateOptions() { if (this.options.fftSize < 32 || this.options.fftSize > 32768) throw new Error('Invalid fftSize'); }
    private configureAnalyser(): void {
        if (!this.analyser) return;
        this.analyser.fftSize = this.options.fftSize;
        this.analyser.minDecibels = this.options.minDecibels;
        this.analyser.maxDecibels = this.options.maxDecibels;
        this.analyser.smoothingTimeConstant = this.options.smoothingTimeConstant;
    }

    public loadAudioFromGPT(s: string, url: string = "http://127.0.0.1:9880/tts") {
        const xhr = new XMLHttpRequest();
        xhr.open("POST", url, true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.responseType = "arraybuffer";

        xhr.addEventListener("loadend", () => {
            this.play(xhr.response);
        });

        xhr.send(JSON.stringify({
            text: s,
            text_lang: "zh",
            ref_audio_path: "output/ssy_的就是，你的能力表现会越接近的话，那你的那个大脑的活动，激活的模式，可能也会越相似。.wav",
            prompt_text: "的就是，你的能力表现会越接近的话，那你的那个大脑的活动，激活的模式，可能也会越相似。",
            prompt_lang: "zh"
        }));
    }

    public play(arrayBuffer: ArrayBuffer) {
        this.isPlaying = true;
        if(!this.audioContext) this.audioContext = new AudioContext();
        this.audioContext.decodeAudioData(arrayBuffer).then(audioBuffer => {
            this.audioContext?.close();
            this.audioContext = new AudioContext();
            if (this.source) {
                this.source.stop();
                this.source = null;
            }

            this.source = this.audioContext.createBufferSource();
            this.analyser = this.audioContext.createAnalyser();
            this.configureAnalyser();
            this.source.buffer = audioBuffer;
            this.source.connect(this.analyser);
            this.source.connect(this.audioContext.destination);
            this.source.addEventListener("ended", () => {
                this.source?.stop();
            });
            this.source.start();
        });
    }
    public stop() {
        if (!this.isPlaying) return;
        this.isPlaying = false;
        this.source?.stop();
    }
    public get status() {
        return this.isPlaying ? "playing" : "stop";
    }
    public get currAudioArray(): Uint8Array {
        if (!this.analyser) return new Uint8Array(this.options.fftSize / 2);
        const data = new Uint8Array(this.analyser.frequencyBinCount);
        this.analyser.getByteFrequencyData(data);
        return data;
    }
}

export class StreamAudioPlayer implements AudioPlayer {
    private audioElement: HTMLAudioElement | null = null;
    private audioContext: AudioContext | null = null;
    private sourceNode: MediaElementAudioSourceNode | null = null;
    private analyser: AnalyserNode | null = null;
    private options: AnalyserOption;

    private isPlaying: boolean = false;
    constructor(options?: Partial<AnalyserOption>) {
        this.options = {
            minDecibels: -90,
            maxDecibels: -10,
            smoothingTimeConstant: 0.8,
            fftSize: 256,
            ...options
        }
        this.validateOptions();
    }
    private validateOptions() {
        if (this.options.fftSize < 32 || this.options.fftSize > 32768) throw new Error('Invalid fftSize');
    }
    private configureAnalyser(): void {
        if (!this.analyser) return;
        this.analyser.fftSize = this.options.fftSize;
        this.analyser.minDecibels = this.options.minDecibels;
        this.analyser.maxDecibels = this.options.maxDecibels;
        this.analyser.smoothingTimeConstant = this.options.smoothingTimeConstant;
    }

    private loadStream(url: string) {
        this.audioElement = new Audio();
        this.audioElement.crossOrigin = "anonymous"; // 允许跨域音频流
        this.audioElement.src = url;
        this.audioElement.loop = false; // 是否循环播放
        this.audioElement.preload = "auto";
        this.audioElement.addEventListener("ended", () => {
            this.stop();
        });

        this.audioContext?.close();
        this.audioContext = new AudioContext();

        this.sourceNode = this.audioContext.createMediaElementSource(this.audioElement);
        this.sourceNode.connect(this.audioContext.destination);

        this.analyser = this.audioContext.createAnalyser();
        this.configureAnalyser();
        this.sourceNode.connect(this.analyser);
    }

    private loadGet(s: string) {
        // ./assets/audio/videoplayback.mp3
        this.loadStream(`http://127.0.0.1:9880/tts?text=${s}&text_lang=zh&ref_audio_path=output/ssy_%E7%9A%84%E5%B0%B1%E6%98%AF%EF%BC%8C%E4%BD%A0%E7%9A%84%E8%83%BD%E5%8A%9B%E8%A1%A8%E7%8E%B0%E4%BC%9A%E8%B6%8A%E6%8E%A5%E8%BF%91%E7%9A%84%E8%AF%9D%EF%BC%8C%E9%82%A3%E4%BD%A0%E7%9A%84%E9%82%A3%E4%B8%AA%E5%A4%A7%E8%84%91%E7%9A%84%E6%B4%BB%E5%8A%A8%EF%BC%8C%E6%BF%80%E6%B4%BB%E7%9A%84%E6%A8%A1%E5%BC%8F%EF%BC%8C%E5%8F%AF%E8%83%BD%E4%B9%9F%E4%BC%9A%E8%B6%8A%E7%9B%B8%E4%BC%BC%E3%80%82.wav&prompt_lang=zh&prompt_text=%E7%9A%84%E5%B0%B1%E6%98%AF%EF%BC%8C%E4%BD%A0%E7%9A%84%E8%83%BD%E5%8A%9B%E8%A1%A8%E7%8E%B0%E4%BC%9A%E8%B6%8A%E6%8E%A5%E8%BF%91%E7%9A%84%E8%AF%9D%EF%BC%8C%E9%82%A3%E4%BD%A0%E7%9A%84%E9%82%A3%E4%B8%AA%E5%A4%A7%E8%84%91%E7%9A%84%E6%B4%BB%E5%8A%A8%EF%BC%8C%E6%BF%80%E6%B4%BB%E7%9A%84%E6%A8%A1%E5%BC%8F%EF%BC%8C%E5%8F%AF%E8%83%BD%E4%B9%9F%E4%BC%9A%E8%B6%8A%E7%9B%B8%E4%BC%BC%E3%80%82&text_split_method=cut5&batch_size=1&media_type=wav&streaming_mode=true`);
        // this.loadStream("./assets/audio/videoplayback.mp3");
    }
    public play(s: string) {
        if (this.isPlaying) {
            this.stop();
        }
        this.loadGet(s);
        this.isPlaying = true;
        this.audioContext?.resume().then(() => {
            this.audioElement?.play();
        });
    }
    public stop() {
        if (!this.isPlaying) return;
        this.isPlaying = false;
        this.sourceNode?.disconnect();
        this.analyser?.disconnect();
        this.audioElement?.pause();
    }

    public get status() {
        return this.isPlaying ? "playing" : "stop";
    }
    public get currAudioArray(): Uint8Array {
        if (!this.analyser) return new Uint8Array(this.options.fftSize / 2);
        const data = new Uint8Array(this.analyser.frequencyBinCount);
        this.analyser.getByteFrequencyData(data);
        return data;
    }
}