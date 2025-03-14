# stage 1
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY ui /app
RUN npm install && npm run build

# stage 2
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
COPY --from=frontend-builder /app/dist /app/ui/dist
RUN chmod +x /app/script/start.sh