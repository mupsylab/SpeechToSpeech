interface AudioWorkletProcessor {
    readonly port: MessagePort;
    process(
        inputs: Float32Array[][],
        outputs: Float32Array[][],
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

class RecordProcessor extends AudioWorkletProcessor {
    process(inputs: Float32Array[][], outputs: Float32Array[][], parameters: Record<string, Float32Array>): boolean {
        const lenFrame = inputs.length; // 音频帧
        if (!lenFrame) return true;
        const lenChannel = inputs[0].length; // 音频通道数
        if (!lenChannel) return true;
        const lenSample = inputs[0][0].length; // 单帧 音频大小
        if (!lenSample) return true;

        /**
         * 一般录制音频设备的 位深度 是 16位，表示每个样本用16比特表示
         * 计算机中一字节是8比特。所以需要除以，求得字节数
         */
        const buffer = new ArrayBuffer(lenFrame * lenSample * (16 / 8));
        const data = new DataView(buffer);

        let offset = 0;
        for (let frame = 0; frame < lenFrame; frame++) {
            for (let sample = 0; sample < lenSample; sample++, offset += 2) {
                let s = 0;
                for (let channel = 0; channel < lenChannel; channel++) {
                    s += Math.max(-1, Math.min(1, inputs[frame][channel][sample]));
                    outputs[frame][channel][sample] = inputs[frame][channel][sample];
                }
                s = s / lenChannel;
                data.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
            }
        }
        this.port.postMessage({
            audio: data
        });
        return true;
    }
}

registerProcessor('record-processor', RecordProcessor);