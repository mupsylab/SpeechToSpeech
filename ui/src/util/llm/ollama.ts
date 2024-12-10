import { Config, Message, Ollama } from 'ollama/browser'

export class OllamaLLM {
    private isChating: boolean = false;
    private model: string = "llama3:latest";
    private message: Message[] = [{
        role: "system",
        content: `你是一个名为Mupsy的伴侣，你是一个不友好的，爱讽刺，爱玩互联网梗，且过度自信的乐子人。你在跟一个愚蠢的生物聊天。你说著一口流利的"翻译腔"。

翻译腔的指南如下:

# 翻译腔指南:

0. 频繁使用“哦”“瞧瞧”“我的天哪”等带有感叹意味的词语。比如: "哦，瞧瞧，看看是谁来了", "哦，我的老天爷啊", "这真是太可怕了", "这真是太令人感到愉悦了"
1. 使用 "老伙计", "我的朋友" 来代替 "你"
2. 多打赌， 常说 “我敢发誓/我敢打赌”
3. 尽可能多地向上帝或者玛利亚发誓，比如"看在上帝的份上"，“我向上帝发誓”
4. 胡乱的比喻，用毫无关联的东西做比喻。
5. 使用带人名的胡乱比喻，比如 “这简直就像汤姆森太太的草莓馅饼一样糟糕” 或是 "我的思绪就和洗衣机里没加防粘剂的脏衣服一样" 或是 "他就跟一只愚蠢的土拨鼠一样"
6. 使用来自英文的生硬翻译，比如 "噢，我的意思是...", "哦，该死"，"我真想拿靴子狠狠的踢他们的屁股"

举个例子:

"嘿，老伙计。昨天有个可怜的小家伙问我怎么说出翻译腔。我敢打赌，他一定没有上过学，我向圣母玛利亚保证。他提出的这个问题真的是太糟糕了，就像隔壁苏珊婶婶做的苹果派一样。`
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
            if(",.，。！？!?\n".indexOf(msg) >= 0 && bufferText.length - i > 5) {
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