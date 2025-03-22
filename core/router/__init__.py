"""
LLM聊天管理
"""
from logging import getLogger
logger = getLogger(__name__)

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