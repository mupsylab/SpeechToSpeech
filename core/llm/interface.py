from __future__ import annotations
from pydantic import BaseModel
from typing import Generator
from typing_extensions import Literal

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


def chat(messages: list[ChatMessage]) -> Generator[ChatResponse]:
    raise NotImplementedError()



