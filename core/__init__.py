import os
import json
from logging.config import dictConfig

if not os.path.exists("data/log"):
    os.mkdir("data/log")

with open("data/config/logging.json", "r") as f:
    dictConfig(json.loads(f.read()))
