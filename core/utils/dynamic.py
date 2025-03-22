from __future__ import annotations
import os
from logging import getLogger
logger = getLogger(__name__)

from typing_extensions import Generator, Callable
StreamIO = Callable[[Generator[str]], Generator[bytes]]

from ..llm import Chat

# 导入llm模块
module = __import__(f"core.llm.{os.getenv('LLM', 'chatgpt')}", globals(), locals(), ["chat"])
chat: Chat = module.chat

# 导入tts模块
module = __import__(f"model.{os.getenv('TTS', 'sovits')}", globals(), locals(), ["stream_io"])
stream_io: StreamIO = module.stream_io

