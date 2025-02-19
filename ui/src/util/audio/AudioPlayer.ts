import { AudioBase } from ".";

export class AudioPlayer extends AudioBase {
    private audioElement: HTMLAudioElement;
    constructor(options?: Partial<AnalyserOptions>) {
        super(options);
        // 创建音频
        const audioElement = new Audio();
        audioElement.crossOrigin = "anonymous"; // 允许跨域音频流
        audioElement.src = "#";
        audioElement.loop = false; // 是否循环
        audioElement.onended = () => { this.stop(); }
        // 创建解析器
        const audioContext = new AudioContext();
        const sourceNode = audioContext.createMediaElementSource(audioElement);
        sourceNode.connect(audioContext.destination);

        this.analyser = audioContext.createAnalyser();
        this.configureAnalyser();
        sourceNode.connect(this.analyser);

        // 结束初始化
        this.audioElement = audioElement;
    }

    load(url: string) {
        if (url == this.audioElement.src) {
            this.audioElement.src = "#";
        }
        this.audioElement.src = url;
    }
    start() {
        this.audioElement.play();
        this.dispatchEvent("start");
    }
    stop() {
        this.audioElement?.pause();
        this.dispatchEvent("stop");
    }
}
