import { AudioBase } from ".";
import RecordProcessor from "./RecordProcessor?worker&url";

export class AudioRecord extends AudioBase {
    private audioContext: AudioContext | undefined;
    private workletNode: AudioWorkletNode | undefined;
    constructor(options?: Partial<AnalyserOptions>) {
        super(options);
    }
    public get sampleRate() {
        return this.audioContext ? this.audioContext.sampleRate : 0;
    }

    private async initAudioContext() {
        if(this.audioContext != undefined) this.audioContext.close();
        // 创建 音频 上下文
        const audioContext = new AudioContext();
        await audioContext.audioWorklet.addModule(RecordProcessor);
        const workletNode = new AudioWorkletNode(audioContext, 'record-processor');

        this.analyser = audioContext.createAnalyser();
        this.configureAnalyser();
        workletNode.connect(this.analyser);

        this.audioContext = audioContext;
        this.workletNode = workletNode;
    }
    private async destoryAudioContext() {
        if(this.audioContext == undefined || this.workletNode == undefined || this.analyser == undefined) return;
        this.analyser?.disconnect();
        this.workletNode.port.postMessage({ action: "intercept" });
        this.workletNode.disconnect();
        this.audioContext.close();
        this.workletNode = undefined;
        this.audioContext = undefined;
        this.analyser = undefined;
    }

    private clean = () => {}
    async start() {
        const stream = await window.navigator.mediaDevices.getUserMedia({ audio: true });
        await this.initAudioContext();
        if (this.audioContext == undefined || this.workletNode == undefined) return;

        const source = this.audioContext.createMediaStreamSource(stream);
        this.analyser = this.audioContext.createAnalyser();
        this.configureAnalyser();
        source.connect(this.analyser);

        const blob: Blob[] = [];
        this.workletNode.port.onmessage =  (e) => {
            blob.push(e.data.audio);
            // 假设采样率 48000，一秒钟48000个样本点
            // 一次会提供 32 个样本
            if (blob.length >= 500) {
                this.dispatchEvent("record", new Blob(blob, { type: "audio/wav" }));
                blob.splice(0, blob.length);
            }
        }
        source.connect(this.workletNode);

        this.clean = () => {
            if (blob.length > 0) {
                this.dispatchEvent("record", new Blob(blob, { type: "audio/wav" }));
                blob.splice(0, blob.length);
            }
            stream?.getTracks().forEach(track => track.stop());
        }
        this.dispatchEvent("start");
    }

    async stop() {
        await this.destoryAudioContext();
        this.clean();
        this.clean = () => {};
        this.dispatchEvent("stop");
    }
}
