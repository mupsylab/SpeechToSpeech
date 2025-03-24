import { int16ToFloat32 } from "./utils";

interface WriteAction { action: "write", audio: Int16Array }
interface InterceptAction { action: "intercept" }
type Action = WriteAction | InterceptAction;

class PlayerProcessor extends AudioWorkletProcessor {
    bufferOutput: Array<Float32Array>;
    bufferIndex: number;
    constructor() {
        super();

        this.bufferOutput = [];
        this.bufferIndex = 0;
        this.port.onmessage = this.handlerMessage.bind(this);
    }

    handlerMessage(e: { data: Action }) {
        if (e.data.action === "write") {
            const float32Array = int16ToFloat32(e.data.audio);
            this.bufferOutput.push(float32Array);
        }
        if (e.data.action === "intercept") {
            this.bufferOutput.splice(0, this.bufferOutput.length);
            this.bufferIndex = 0;
        }
    }

    process(_inputs: Array<Array<Float32Array>>, outputs: Array<Array<Float32Array>>, _params: Record<string, Float32Array>): boolean {
        const lenDevice = outputs.length;
        if (lenDevice === 0) return true;
        const lenChannel = outputs[0].length;
        if (lenChannel === 0) return true;
        const lenFrame = outputs[0][0].length;
        if (lenFrame === 0) return true;

        if (this.bufferOutput.length === 0) return true;
        for (let device = 0; device < lenDevice; device++) {
            for (let frame = 0; frame < lenFrame; frame++) {
                while (true) {
                    if (this.bufferOutput.length === 0) return true;
                    if (this.bufferIndex >= this.bufferOutput[0].length) {
                        this.bufferIndex -= this.bufferOutput[0].length;
                        this.bufferOutput.shift(); // 删除第一个
                    } else {
                        break;
                    }
                }
                const sample = this.bufferOutput[0][this.bufferIndex++];
                for (let channel = 0; channel < lenChannel; channel++) {
                    outputs[device][channel][frame] = sample;
                }
            }
        }
        return true;
    }
}

registerProcessor('player-processor', PlayerProcessor);

interface AudioWorkletProcessor {
    readonly port: MessagePort;
    process(
        inputs: Array<Array<Float32Array>>,
        outputs: Array<Array<Float32Array>>,
        parameters: Record<string, Float32Array>
    ): boolean;
}

declare var AudioWorkletProcessor: {
    prototype: AudioWorkletProcessor;
    new(options?: AudioWorkletNodeOptions): AudioWorkletProcessor;
};

declare function registerProcessor(
    name: string,
    processorCtor: (new (
        options?: AudioWorkletNodeOptions
    ) => AudioWorkletProcessor)
): void;
