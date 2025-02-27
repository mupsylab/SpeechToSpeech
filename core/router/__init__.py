"""
LLM聊天管理
"""
from ..llm import ChatManager
from ..llm.chatgpt import chat
cm = ChatManager()
def generate_msg():
    if len(cm.cache) and cm.cache[-1].role == "assistant":
        yield cm.cache[-1].content
    else:
        for resp in chat(cm.get_llm_message()):
            if resp.type == "sentence":
                yield resp.content
        cm.add_chat(resp.content, "assistant")
