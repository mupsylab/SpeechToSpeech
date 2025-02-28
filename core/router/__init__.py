"""
LLM聊天管理
"""
import os
from logging import getLogger
logger = getLogger(__name__)
from ..llm import ChatManager
from ..llm import Chat

module = __import__(f"core.llm.{os.getenv('LLM', 'chatgpt')}", globals(), locals(), ["chat"])
chat: Chat = module.chat

cm = ChatManager()
def generate_msg():
    if len(cm.cache) and cm.cache[-1].role == "assistant":
        yield cm.cache[-1].content
    else:
        for resp in chat(cm.get_llm_message()):
            if resp.type == "sentence":
                logger.debug("start generate llm sentence: %s" % resp.content)
                yield resp.content
        cm.add_chat(resp.content, "assistant")
