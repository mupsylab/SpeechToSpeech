from pydantic import BaseModel
from typing_extensions import Literal

class ChatMessage(BaseModel):
    role: Literal[
        "system",
        "assistant",
        "user"
    ]
    content: str