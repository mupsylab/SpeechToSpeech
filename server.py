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

from fastapi.responses import HTMLResponse
@app.get("/", response_class = HTMLResponse)
async def read_index():
    with open("ui/dist/index.html", "rb") as f:
        b = f.read()
    return HTMLResponse(content = b)
app.mount("/", StaticFiles(directory="ui/dist"), name = "static")

if __name__ == "__main__":
    import json
    import uvicorn
    from logging.config import dictConfig
    with open("data/config/logging.json", "r") as f:
        config = json.loads(f.read())
    dictConfig(config)

    if not os.path.exists("data/log"):
        os.mkdir("data/log")

    uvicorn.run(app, 
                host=os.getenv("HOST", "0.0.0.0"), 
                port=int(os.getenv("PORT", "8000")),
                log_config=config)
