import os
import uvicorn
from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    uvicorn.run("api:app", host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", 8002)))
