import { AudioUtils } from "./AudioUtils";
import { EventManager } from "../EventManager";
interface Audio {
    currAudioArray: Uint8Array;
}
interface AudioRecord extends Audio {
    status: 'stop' | 'recording' | 'prepare';
}
interface AnalyserOption {
    fftSize: number;
    smoothingTimeConstant: number;
    minDecibels: number;
    maxDecibels: number;
};
interface StreamAudioOption {
    recordDuation: number;
    recordInterval: number;
    silenceThreshold: number;
}

export class BaseAudioRecord extends EventManager implements AudioRecord {
    private stream: MediaStream | null = null;
    private mediaRecorder: MediaRecorder | null = null;
    private audioContext: AudioContext | null = null;
    private analyser: AnalyserNode | null = null;

    private options: AnalyserOption;

    private isInit: boolean = false;
    private isRecording: boolean = false;

    constructor(options?: Partial<AnalyserOption>) {
        super();

        this.options = {
            minDecibels: -90,
            maxDecibels: -10,
            smoothingTimeConstant: 0.8,
            fftSize: 256,
            ...options
        };
        this.validateOptions();
    }

    private validateOptions() {
        if (this.options.fftSize < 32 || this.options.fftSize > 32768) throw new Error('Invalid fftSize');
        // 添加其他必要的参数验证
    }
    private configureAnalyser(): void {
        if (!this.analyser) return;

        this.analyser.fftSize = this.options.fftSize;
        this.analyser.minDecibels = this.options.minDecibels;
        this.analyser.maxDecibels = this.options.maxDecibels;
        this.analyser.smoothingTimeConstant = this.options.smoothingTimeConstant;
    }

    private startRecording(): void {
        if (this.isRecording || !this.mediaRecorder) return;
        this.isRecording = true;
        this.mediaRecorder.start(1000);
    }

    private stopRecording(): void {
        if (!this.isRecording || !this.mediaRecorder) return;
        this.isRecording = false;
        this.mediaRecorder.stop();
    }

    private audioChunks: Blob[] = [];
    private registerEventListener() {
        if (!this.mediaRecorder) return;
        this.mediaRecorder.addEventListener("dataavailable", (e) => {
            this.audioChunks.push(e.data);
        });
        this.mediaRecorder.addEventListener("stop", () => {
            if (this.audioChunks.length == 0) return;
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
            AudioUtils.getAudioBufferFromBlob(audioBlob).then(arrayBuffer => {
                const blob = new Blob([AudioUtils.audioBufferToWav(arrayBuffer)], { type: "audio/wav" });
                this.dispatchEvent("record", blob);
                this.audioChunks = [];
            });
        });
    };

    public async start(): Promise<void> {
        if (this.isInit) return;

        try {
            const stream = await window.navigator.mediaDevices.getUserMedia({ audio: true });

            this.stream = stream;
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioContext = new AudioContext();

            const source = this.audioContext.createMediaStreamSource(stream);
            this.analyser = this.audioContext.createAnalyser();
            this.configureAnalyser();
            source.connect(this.analyser);

            this.registerEventListener();
            this.isInit = true;
            this.dispatchEvent("start");
            this.startRecording();
        } catch (error) {
            console.error('Failed to initialize audio recording:', error);
            throw error;
        }
    }

    public stop(): void {
        if (!this.isInit) return;

        this.dispatchEvent("stop");
        this.stopRecording();
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }

        this.isInit = false;
        this.analyser?.disconnect();
        this.analyser = null;
        this.audioContext?.close();
        this.audioContext = null;
        this.stream = null;
        this.mediaRecorder = null;
    }

    public get status() {
        if (!this.isInit) return "stop";
        if (this.isRecording) return "recording";
        return "prepare";
    }

    public get currAudioArray(): Uint8Array {
        if (!this.analyser) return new Uint8Array(128);
        const data = new Uint8Array(this.analyser.frequencyBinCount);
        this.analyser.getByteFrequencyData(data);
        return data;
    }
}

export class StreamAudioRecord extends EventManager implements AudioRecord {
    private stream: MediaStream | null = null;
    private mediaRecorder: MediaRecorder | null = null;
    private audioContext: AudioContext | null = null;
    private analyser: AnalyserNode | null = null;

    private options: AnalyserOption & StreamAudioOption;
    private validateOptions() {
        if (this.options.fftSize < 32 || this.options.fftSize > 32768) throw new Error('Invalid fftSize');
        // 添加其他必要的参数验证
    }
    private configureAnalyser(): void {
        if (!this.analyser) return;

        this.analyser.fftSize = this.options.fftSize;
        this.analyser.minDecibels = this.options.minDecibels;
        this.analyser.maxDecibels = this.options.maxDecibels;
        this.analyser.smoothingTimeConstant = this.options.smoothingTimeConstant;
    }

    private isRecording: boolean = false;
    constructor(options?: Partial<AnalyserOption & StreamAudioOption>) {
        super();

        this.options = {
            recordInterval: 100,
            recordDuation: 2000,
            silenceThreshold: 20,
            minDecibels: -90,
            maxDecibels: -10,
            smoothingTimeConstant: 0.8,
            fftSize: 256,
            ...options
        };
        this.validateOptions();
    }

    private audioChunks: Blob[] = [];
    private registerEventListener() {
        if (!this.mediaRecorder) return;
        this.mediaRecorder.addEventListener("dataavailable", (e) => {
            this.audioChunks.push(e.data);
        });
    };
    private registerContext() {
        if (!this.stream) return;
        this.audioContext = new AudioContext();
        const source = this.audioContext.createMediaStreamSource(this.stream);
        this.analyser = this.audioContext.createAnalyser();
        this.configureAnalyser();
        source.connect(this.analyser);
    }
    private saveAudio() {
        if (this.audioChunks.length == 0) return;
        Promise.all(this.audioChunks.map(AudioUtils.getAudioBufferFromBlob)).then(r => {
            const arrayBuffer = AudioUtils.mergeAudioBuffer(r);
            const blob = new Blob([AudioUtils.audioBufferToWav(arrayBuffer)], { type: "audio/wav" });
            this.dispatchEvent("record", blob);
        });
        this.audioChunks = [];
    }
    private timerHandler() {
        this.mediaRecorder?.stop();
        const len = this.options.recordDuation / this.options.recordInterval;
        if ((this.audioChunks.length > len && !this.detectSound) || !this.isRecording) {
            // 如果 音频长度 达到最大, 且没人在说话
            // 或 结尾没人说话
            // 则保持音频
            this.saveAudio();

            if (!this.isRecording) {
                clearInterval(this.recordIntervalNumber);
            }
        }
        if (this.isRecording && this.mediaRecorder?.state == 'inactive') {
            // 如果正在记录的话, 重新录制
            this.mediaRecorder?.start();
        }
    }

    private recordIntervalNumber: number = -1;
    public start() {
        if (this.isRecording) return;
        if (!window.navigator.mediaDevices) return;
        window.navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
            this.stream = stream;
            this.mediaRecorder = new MediaRecorder(stream);
            this.registerContext();
            this.registerEventListener();
            this.isRecording = true;
            this.dispatchEvent("start");
            this.mediaRecorder.start();
            this.recordIntervalNumber = setInterval(() => {
                this.timerHandler();
            }, this.options.recordInterval) as unknown as number;
        }).catch(e => {
            console.log(e);
        })
    }
    public stop() {
        if (!this.isRecording || !this.mediaRecorder) return;
        this.isRecording = false;

        this.dispatchEvent("stop");
        this.mediaRecorder.stop();
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }

        this.analyser?.disconnect();
        this.analyser = null;
        this.audioContext?.close();
        this.audioContext = null;
        this.stream = null;
        this.mediaRecorder = null;
    }

    public get detectSound() {
        if (!this.analyser) return false;
        const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
        this.analyser.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((acc, value) => acc + value, 0) / dataArray.length;
        return average > this.options.silenceThreshold;
    }
    public get status() {
        return this.isRecording ? "recording" : "stop";
    }
    public get currAudioArray(): Uint8Array {
        if (!this.analyser) return new Uint8Array(this.options.fftSize / 2);
        const data = new Uint8Array(this.analyser.frequencyBinCount);
        this.analyser.getByteFrequencyData(data);
        return data;
    }
}