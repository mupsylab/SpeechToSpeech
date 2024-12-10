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

    public play(arrayBuffer: ArrayBuffer) {
        if (this.isPlaying) this.stop();
        if(!this.audioContext) this.audioContext = new AudioContext();

        this.isPlaying = true;
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

    private startListener: Function[] = [];
    private stopListener: Function[] = [];
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

    public waitStart() {
        return new Promise((resolve) => {
            if(this.isPlaying) resolve(undefined);
            this.startListener.push(() => { resolve(undefined); });
        });
    }
    public waitStop() {
        return new Promise((resolve) => {
            if(!this.isPlaying) resolve(undefined);
            this.stopListener.push(() => { resolve(undefined); });
        });
    }
    public play(url: string) {
        if (this.isPlaying) {
            this.stop();
        }
        for(const listener of this.startListener) {
            listener();
        }
        this.startListener = [];
        this.loadStream(url);
        this.isPlaying = true;
        this.audioContext?.resume().then(() => {
            this.audioElement?.play();
        });
    }
    public stop() {
        if (!this.isPlaying) return;
        for(const listener of this.stopListener) {
            listener();
        }
        this.stopListener = [];
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