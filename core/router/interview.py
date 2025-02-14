from __future__ import annotations
from typing import Annotated
import fastapi
from fastapi.responses import StreamingResponse

router = fastapi.APIRouter(prefix = "/api")

from core.llm.chatgpt import chat
from core.utils.snowflake import generate_snowflake_id
from core.interview import InterviewManager

cache: dict[int, InterviewManager] = {}

@router.put("/llm/interview")
async def put_llm(msg: Annotated[str, fastapi.Form()],
                  cid: Annotated[int, fastapi.Form()] = None):
    if not isinstance(cid, int):
       cid = int(cid) 
    if cid is None:
        cid = generate_snowflake_id()
    if cid not in cache:
        cache[cid] = InterviewManager(cid)
    im = cache[cid]
    im.add_chat(msg, "user")
    im.save_data(im.data)
    return fastapi.Response(str(cid))

@router.get("/llm/interview")
async def get_llm(cid: Annotated[int, fastapi.Form()] = None):
    return StreamingResponse(
        generate_msg(cid)
    )

def generate_msg(cid: int = None):
    if not isinstance(cid, int):
       cid = int(cid)
    if cid is None:
        cid = generate_snowflake_id()
    if cid not in cache:
        cache[cid] = InterviewManager(cid)
    im = cache[cid]
    if len(im.data.messages) and im.data.messages[-1].role == "assistant":
        yield im.data.messages[-1].content
    else:
        for resp in chat(im.get_llm_message()):
            if resp.type == "sentence":
                yield resp.content
        im.add_chat(resp.content, "assistant")
        im.save_data(im.data)



