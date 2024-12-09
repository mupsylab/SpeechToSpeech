import { Config, Message, Ollama } from 'ollama/browser'

export class OllamaLLM {
    private isChating: boolean = false;
    private model: string = "llama3:latest";
    private message: Message[] = [{
        role: "system",
        content: "你是一个陪伴聊天的友人, 你接下来的回答都应该使用中文。且回答中不要出现“哈哈”"
    }];

    private ollama: Ollama;
    /**
     * 在llm开始恢复的时候进行调用, 以便于进行初始化的操作
     */
    private init_callback: () => void;
    /**
     * 当需要流式输出的时候，利用回调函数输出llm的信息
     */
    private callback: (msg: string) => void;
    constructor(config: Config, callback: (msg: string) => void, init_callback: () => void) {
        this.ollama = new Ollama(config);
        this.callback = callback;
        this.init_callback = init_callback;
    }

    private stopListener: Function[] = [];
    waitStop() {
        return new Promise((resolve) => {
            if(!this.isChating) resolve(undefined);
            this.stopListener.push(() => { resolve(undefined); });
        });
    }
    async chat(msg: string) {
        await this.waitStop();
        this.message.push({
            role: 'user',
            content: msg
        });
        const response = await this.ollama.chat({
            model: this.model,
            messages: this.message,
            stream: true
        });

        const bufferText: string[] = [];
        let i = 0;
        this.init_callback();
        for await (const part of response) {
            const msg = part.message.content;

            bufferText.push(msg);
            if(",.，。！？!?\n".indexOf(msg) >= 0) {
                this.callback(bufferText.slice(i, bufferText.length).join(""));
                i = bufferText.length;
            }
        }
        if(i < bufferText.length) {
            this.callback(bufferText.slice(i, bufferText.length).join(""));
        }
        this.message.push({
            role: 'assistant',
            content: bufferText.join("")
        });

        for(const listener of this.stopListener) {
            listener();
        }
        this.stopListener = [];
    }
}