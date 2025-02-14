import os
import fastapi
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
load_dotenv()

ENABLE = os.getenv("ENABLE", "websocket").split(",")
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
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
