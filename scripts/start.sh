#!/bin/bash

# 环境安装
FLAG_ENV_FILE="/app/env/.installed"
# 模型下载安装
FLAG_MODEL_FILE="/app/model_pretrained/.installed"

if [ ! -f "$FLAG_ENV_FILE" ]; then
    echo "Installing dependencies..."

    apt-get update -y && apt-get upgrade -y && apt-get install gcc g++ ffmpeg -y

    pip install --upgrade pip
    pip install numpy==1.23.4 -t /app/env
    pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu124 -t /app/env
    pip install -r requirements.txt -t /app/env

    touch "$FLAG_ENV_FILE"
    echo "Dependencies installed."
else
    echo "Dependencies already installed."
fi

if [ ! -f "$FLAG_MODEL_FILE" ]; then
    echo "Installing model..."

    python script/download.py
    pip install -t /app/env /app/model_pretrained/CosyVoice-ttsfrd/ttsfrd-0.4.2-cp310-cp310-linux_x86_64.whl

    touch "$FLAG_MODEL_FILE"
    echo "Model installed."
else
    echo "Model already installed."
fi

python server.py
