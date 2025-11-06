# path: backend/Dockerfile
# version: v0.20
FROM python:3.11-slim-bookworm

WORKDIR /app

COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y net-tools grep -y # Install net-tools and grep

COPY backend/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
