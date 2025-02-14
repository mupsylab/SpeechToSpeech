from __future__ import annotations
import os
import re
import openai
from typing import Generator

from .interface import ChatResponse, ChatMessage

client = openai.OpenAI(
    base_url = os.getenv("OPENAI_BASE_URL", None),
    api_key  = os.getenv("OPENAI_API_KEY", None)
)

def chat(messages: list[ChatMessage]) -> Generator[ChatResponse]:
    response = client.chat.completions.create(
        model = os.getenv("OPENAI_MODEL", None),
        messages = messages,
        max_tokens = 8192,
        temperature = 0.7,
        stream = True
    )

    # 因为用流式处理，需要进行断句。当一句完成后再返回。
    # 最后将整个句子保存
    global_content = []
    content = []
    for resp in response:
        c: str = resp.choices[0].delta.content
        if c is None:
            continue
        global_content.append(c)
        yield ChatResponse(type = "char", content = c)

        pattern = re.search(r"[,\.!\?，。？！、]", c)
        if pattern and len("".join(content).strip()) > 10:
            [spos, epos] = pattern.span()
            if spos == 0:
                # 分段的时候在开头
                msg = "".join(content) + c[spos]
                content = [c[spos:]] if len(c) > 1 else []
            elif epos == len(c):
                # 分段的时候在结尾
                msg = "".join(content + [c])
                content = []
            else:
                # 分段在中间
                [stext, etext] = c.split(c[spos])
                msg = "".join(content + [f"{stext}{c[spos]}"])
                content = [etext]
            yield ChatResponse(type = "sentence", content = msg)
        else:
            content.append(c)
    if len(content):
        # 还有剩下的内容
        yield ChatResponse(type = "sentence", content = "".join(content))

    yield ChatResponse(type = "finish", content = "".join(global_content))



