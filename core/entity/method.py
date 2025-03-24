import numpy as np
from typing_extensions import Literal, List, Generator, Callable
from .chat_message import ChatMessage
from .chat_response import ChatResponse

Chat = Callable[[List[ChatMessage]], Generator[ChatResponse]]
StreamIO = Callable[[str], Generator[tuple[np.ndarray, int]]]
