"""
LLM聊天管理
"""
import os
from ..llm import ChatManager

module = __import__(f"core.llm.{os.getenv('LLM', 'chatgpt')}", globals(), locals(), ["chat"])
chat = module.chat

cm = ChatManager()
def generate_msg():
    if len(cm.cache) and cm.cache[-1].role == "assistant":
        yield cm.cache[-1].content
    else:
        for resp in chat(cm.get_llm_message()):
            if resp.type == "sentence":
                yield resp.content
        cm.add_chat(resp.content, "assistant")
