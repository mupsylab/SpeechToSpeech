from typing_extensions import Literal
from pydantic import BaseModel

class WebsocketMessage(BaseModel):
    action: Literal["init", "record", "finish"]
    param: dict[str, str | int] = {}
