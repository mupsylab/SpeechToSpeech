import { AudioBase } from ".";
import PlayerProcessor from "./PlayerProcessor?worker&url";

export class AudioPlayer extends AudioBase {
    private audioContext: AudioContext | undefined;
    private workletNode: AudioWorkletNode | undefined;
    constructor(options?: Partial<AnalyserOptions>) {
        super(options);
    }
    public get sampleRate() {
        return this.audioContext ? this.audioContext.sampleRate : 0;
    }

    private async initAudioContext() {
        if(this.audioContext != undefined || this.workletNode != undefined) return;
        // 创建 音频 上下文
        const audioContext = new AudioContext();
        await audioContext.audioWorklet.addModule(PlayerProcessor);
        const workletNode = new AudioWorkletNode(audioContext, 'player-processor');
        workletNode.connect(audioContext.destination);

        this.analyser = audioContext.createAnalyser();
        this.configureAnalyser();
        // workletNode.connect(this.analyser);

        this.audioContext = audioContext;
        this.workletNode = workletNode;
    }
    private async destoryAudioContext() {
        if(this.audioContext == undefined || this.workletNode == undefined) return;
        this.analyser?.disconnect();
        this.workletNode.port.postMessage({ action: "intercept" });
        this.workletNode.disconnect();
        this.audioContext.close();
        this.workletNode = undefined;
        this.audioContext = undefined;
        this.analyser = undefined;
    }

    clear() {
        this.workletNode?.port.postMessage({
            action: "intercept"
        })
    }
    load(buffer: ArrayBuffer) {
        this.workletNode?.port.postMessage({
            action: "write",
            audio: new Int16Array(buffer)
        })
    }
    async start() {
        await this.initAudioContext();
        this.dispatchEvent("start");
    }
    async stop() {
        await this.destoryAudioContext();
        this.dispatchEvent("stop");
    }
}
