from pydantic import BaseModel
from typing_extensions import Literal

class ChatResponse(BaseModel):
    type: Literal[
        "char",
        "sentence",
        "finish"
    ]
    content: str
