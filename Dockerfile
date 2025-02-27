# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.10-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

RUN apt-get update -y && apt-get upgrade -y && apt-get install gcc g++ ffmpeg -y
COPY model_pretrained /app/model_pretrained
COPY core /app/core
COPY data /app/data
COPY ui/dist /app/ui/dist
COPY requirements.txt /app/requirements.txt
COPY server.py /app/server.py

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
WORKDIR /app
RUN adduser -u 5678 --disabled-password --gecos "" sts && chown -R sts /app
USER sts

# Install pip requirements
RUN pip install --upgrade pip
RUN pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu124
RUN python -m pip install -r requirements.txt

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "-k", "uvicorn.workers.UvicornWorker", "core.router/sovits:app"]
CMD ["python", "server.py"]
EXPOSE 8000
