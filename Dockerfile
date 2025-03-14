# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.10-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

ENV PYTHONPATH=/app/env
WORKDIR /app
EXPOSE 8000
ENTRYPOINT ["/app/script/start.sh"]

COPY . /app
RUN chmod +x /app/script/start.sh