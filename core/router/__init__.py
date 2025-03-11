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
