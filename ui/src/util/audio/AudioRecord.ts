import { AudioBase } from ".";
import RecordProcessor from "./RecordProcessor?url";

export class BaseAudioRecord extends AudioBase {
    private audioContext: AudioContext;
    constructor(options?: Partial<AnalyserOptions>) {
        super(options);
        this.audioContext = new AudioContext();
    }

    private clean = () => {}
    start() {
        window.navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                const source = this.audioContext.createMediaStreamSource(stream);
                this.analyser = this.audioContext.createAnalyser();
                this.configureAnalyser();
                source.connect(this.analyser);

                const mr = new MediaRecorder(stream);
                const blob: Blob[] = [];
                mr.addEventListener("dataavailable", (e) => {
                    blob.push(e.data);
                });
                mr.addEventListener("stop", () => {
                    const audioBlob = new Blob(blob, { type: "audio/webm" });
                    this.dispatchEvent("record", audioBlob);
                });
                mr.start(1000);

                this.clean = () => {
                    source.disconnect();
                    this.analyser?.disconnect();
                    stream?.getTracks().forEach(track => track.stop());
                    mr.stop();

                    this.dispatchEvent("stop");
                }
            })
            .catch(e => {
                this.dispatchEvent("error", e);
            });
    }
    stop() {
        this.clean();
        this.clean = () => {};
    }
}

export class StreamAudioRecord extends AudioBase {
    private audioContext: AudioContext;
    constructor(options?: Partial<AnalyserOptions>) {
        super(options);
        this.audioContext = new AudioContext();

        this.audioContext.audioWorklet.addModule(RecordProcessor)
    }
    public get sampleRate() {
        return this.audioContext.sampleRate;
    }

    private clean = () => {}
    start() {
        window.navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                const source = this.audioContext.createMediaStreamSource(stream);
                this.analyser = this.audioContext.createAnalyser();
                this.configureAnalyser();
                source.connect(this.analyser);

                const blob: Blob[] = [];
                const workletNode = new AudioWorkletNode(this.audioContext, "record-processor");
                workletNode.port.onmessage =  (e) => {
                    blob.push(e.data.audio);
                    // 假设采样率 48000，一秒钟48000个样本点
                    // 一次会提供 32 个样本
                    if (blob.length >= 500) {
                        this.dispatchEvent("record", new Blob(blob, { type: "audio/wav" }));
                        blob.splice(0, blob.length);
                    }
                }
                source.connect(workletNode);

                this.clean = () => {
                    if (blob.length > 0) {
                        this.dispatchEvent("record", new Blob(blob, { type: "audio/wav" }));
                        blob.splice(0, blob.length);
                    }
                    workletNode.disconnect();
                    source.disconnect();
                    this.analyser?.disconnect();
                    stream?.getTracks().forEach(track => track.stop());

                    this.dispatchEvent("stop");
                }
            })
            .catch(e => {
                this.dispatchEvent("error", e);
            });
    }

    stop() {
        this.clean();
        this.clean = () => {};
    }
}
