import { EventManager } from "../EventManager";

export class AudioBase extends EventManager {
    private options: AnalyserOptions;
    constructor(options?: Partial<AnalyserOptions>) {
        super();
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
        const { fftSize } = (this.options as {
            fftSize: number
        });
        if (fftSize < 32 || fftSize > 32768) throw new Error('Invalid fftSize');
    }

    protected analyser: AnalyserNode | undefined;
    protected configureAnalyser(): void {
        const { fftSize, minDecibels, maxDecibels, smoothingTimeConstant } = (this.options as {
            minDecibels: number,
            maxDecibels: number,
            smoothingTimeConstant: number,
            fftSize: number
        });
        if (!this.analyser) return;
        this.analyser.fftSize = fftSize;
        this.analyser.minDecibels = minDecibels;
        this.analyser.maxDecibels = maxDecibels;
        this.analyser.smoothingTimeConstant = smoothingTimeConstant;
    }

    public get currAudioArray(): Uint8Array {
        if (!this.analyser) return new Uint8Array((this.options.fftSize as number) / 2);
        const data = new Uint8Array(this.analyser.frequencyBinCount);
        this.analyser.getByteFrequencyData(data);
        return data;
    }

    start() { throw new Error("No Implement method"); }
    stop() { throw new Error("No Implement method"); }
}