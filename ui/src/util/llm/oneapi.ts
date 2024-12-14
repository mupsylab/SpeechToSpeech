import OpenAI from "openai";
import { ChatCompletionMessageParam } from "openai/resources/chat/completions";

export class OneAPI {
    private isChating: boolean = false;

    private model: string = "";
    private messages: ChatCompletionMessageParam[] = [];
    private openai: OpenAI = new OpenAI({
        baseURL: "",
        apiKey: ""
    });;
    /**
     * 在llm开始恢复的时候进行调用, 以便于进行初始化的操作
     */
    private init_callback: () => void;
    /**
     * 当需要流式输出的时候，利用回调函数输出llm的信息
     */
    private callback: (msg: string) => void;
    constructor(callback: (msg: string) => void, init_callback: () => void) {
        this.init_callback = init_callback;
        this.callback = callback;
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
        this.isChating = true;
        this.messages.push({
            role: 'user',
            content: msg
        });
        const response = await this.openai.chat.completions.create({
            model: this.model,
            messages: this.messages,
            stream: true
        });

        const bufferText: string[] = [];
        let i = 0;
        this.init_callback();
        for await (const chunk of response) {
            const msg = chunk.choices[0].delta.content;
            if(!msg) return;
            bufferText.push(msg);
            if(",.，。！？!?\n".indexOf(msg) >= 0 && bufferText.length - i > 5) {
                this.callback(bufferText.slice(i, bufferText.length).join(""));
                i = bufferText.length;
            }
        }
        if(i < bufferText.length) {
            this.callback(bufferText.slice(i, bufferText.length).join(""));
        }
        this.messages.push({
            role: 'assistant',
            content: bufferText.join("")
        });

        this.isChating = false;
        for(const listener of this.stopListener) {
            listener();
        }
        this.stopListener = [];
    }
}