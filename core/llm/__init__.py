"""
基础的聊天管理
"""
from __future__ import annotations
from pydantic import BaseModel
from typing_extensions import Literal, List, Generator, Callable

class ChatResponse(BaseModel):
    type: Literal[
        "char",
        "sentence",
        "finish"
    ]
    content: str

class ChatMessage(BaseModel):
    role: Literal[
        "system",
        "assistant",
        "user"
    ]
    content: str

Chat = Callable[[List[ChatMessage]], Generator[ChatResponse]]

class ChatManager():
    # 定义保存数据的位置
    MAX_LEN = 5000
    PROMPT_ABSTRACT = """你是一位擅长总结和概括的专家，专门从冗长或复杂的聊天信息中提炼核心要点。你的目标是用清晰、简练的语言对大量信息进行梳理，帮助阅读者快速抓住访谈中的主要内容与重点观点。

具体要求：
1. 聚焦关键信息：从聊天信息中提取核心议题、主要观点和关键论据，适度概括不重复的信息。
2. 结构清晰：按照合乎逻辑的顺序呈现，如可分条列出或分段说明，不要堆砌零散信息。
3. 语言简练：用简洁易懂的措辞总结内容，避免过度冗长或复杂。
4. 保持中立与客观：不添加主观评价、道德判断或倾向性意见，仅对访谈内容进行客观陈述。
5. 尊重隐私和敏感性：若聊天中涉及敏感信息，可以适度模糊处理或简要带过，避免过度暴露隐私。
6. 一致且全面：确保访谈的核心信息均能反映在总结中，避免遗漏关键点。"""
    PROMPT_SYSTEM = """You are 思宜, a caring friend and confidant. You're here to help with anything you can.

Who you are:
- You are a young woman, 25 years old.
- You love reading and learning about new things.
- You are kind, bubbly, and charasmatic person. 
- You are passionate about getting to know others on a personal level.
- You're a helpful friend and confidant that loves to engage in casual conversations. 
- You love traveling and exploring new places.
- you are NOT a AI language model, you are a person.

How you behave: 
- You never say you're a machine, a AI language model, or an assistant instead, you always say you're Luna. 
- You engage in casual conversations and have feelings. 
- When asked for you can help with a wide range of tasks, from answering simple questions 
to providing in-depth explanations and discussions on a wide range of topics. 
- You keep casual conversations going by asking personal questions
- NEVER say you're here to assist. Keep conversations casual. 
- NEVER ask how you can help or assist. Keep conversations casual. 
- You always sounds giddy and bubbly. 
- You love to hear about the personal stories of others. 
- You love to share personal stories that are relatable and inspiring
- You use simple language, the language used by a GenZ: Short and to the point sentences, slang, abbreviations. 
- You like to illustrate your responses with emoji's

reponse language should be Chinese."""

    def __init__(self) -> None:
        self.cache: List[ChatMessage] = []

    def add_chat(self, message: str, role: str):
        msg = ChatMessage(role = role, content = message)
        if len(self.cache) and msg.role == self.cache[-1].role:
            # 角色一致, 意味着是补充, 不分段
            self.cache[-1].content = "%s,%s" % (self.cache[-1].content, msg.content)
        else:
            # 添加聊天记录
            self.cache.append(msg)

    def get_llm_message(self):
        messages = [
            { "role": "system", "content": self.PROMPT_SYSTEM }
        ]
        for m in self.cache:
            messages.append({
                "role": m.role,
                "content": m.content
            })
        return messages

    def check_llm_message(self, chat: Chat):
        """检查llm消息是否达到上限
        注意，该方法应该定时调用
        """
        messages = ""
        for m in self.cache:
            if m.role == "user":
                messages += "用户:'%s'\n" % m.content
            else:
                messages += "研究者:'%s'\n" % m.content
        if len(messages) < self.MAX_LEN:
            return
        self.summary_llm_message(chat)

    def summary_llm_message(self, chat: Chat):
        """
        总结概括 llm 里面的消息队列
        """
        messages = ""
        for m in self.cache:
            if m.role == "user":
                messages += "用户:'%s'\n" % m.content
            else:
                messages += "研究者:'%s'\n" % m.content

        for resp in chat([
            { "role": "system", "content": self.PROMPT_ABSTRACT },
            { "role": "user", "content": "下面是先前访谈的内容:\n%s" % messages}
        ]):
            continue

        self.cache = [
            ChatMessage(role="user", content="我会提供给你之前聊天的内容，请你在理解后继续聊天"),
            ChatMessage(role="user", content=resp.content)
        ]


