import os
import fastapi
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
load_dotenv()

ENABLE = os.getenv("ENABLE", "sts").split(",")
app = fastapi.FastAPI()
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境中使用
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for m in ENABLE:
    module = __import__("core.router.{}".format(m), globals(), locals(), ["router"], 0)
    app.include_router(module.router)

app.mount("/", StaticFiles(directory="ui/dist"), name = "static")
if __name__ == "__main__":
    import time
    import threading

    from core.llm.chatgpt import chat
    from core.router.interview import cache
    def timeHandler():
        # 定时任务
        while True:
            for key, item in cache.items():
                print("check: %s" % str(key))
                item.check_llm_message(chat)
                item.judge(chat)
            time.sleep(30) # 30s 执行一次
    thread = threading.Thread(target=timeHandler, daemon=True)
    thread.start()

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
