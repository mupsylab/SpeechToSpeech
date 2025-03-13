"""
LLM聊天管理
"""
from __future__ import annotations
from typing_extensions import Any, Literal, List, Generator, Callable
StreamIO = Callable[[Generator[str]], Generator[bytes]]

import os
from logging import getLogger
logger = getLogger(__name__)
from ..llm import Chat, ChatManager

# 导入llm模块
module = __import__(f"core.llm.{os.getenv('LLM', 'chatgpt')}", globals(), locals(), ["chat"])
chat: Chat = module.chat

# 导入tts模块
module = __import__(f"model.{os.getenv('TTS', 'sovits')}", globals(), locals(), ["stream_io"])
stream_io: StreamIO = module.stream_io

class SessionManager():
    def __init__(self) -> None:
        self.session: dict[str, dict[str, any]] = {}

    def get(self, key: str | int) -> dict[str, any]:
        if key is None:
            return None
        key = str(key)
        return self.session.get(key, None)

    def set(self, key: str | int, value: dict[str, any] = {}) -> None:
        key = str(key)
        self.session[key] = value
        return key

    def exist(self, key: str | int) -> bool:
        key = str(key)
        return key in self.session

    def delete(self, key: str | int) -> None:
        key = str(key)
        if key in self.session:
            del self.session[key]
        return key
session_manager = SessionManager()

# import threading
# import time
# def timeHandler():
#     while True:
#         for key, item in session_manager.session.items():
#             logger.debug("run session: %s" % key)
#             if "chat" in item:
#                 im: InterviewManager = item["chat"]
#                 im.check_llm_message(chat)
#                 if im.judge(chat):
#                     im.next()
#         time.sleep(30)

# thread = threading.Thread(
#     target=timeHandler,
#     daemon=True
# )
# thread.start()