# Build from repository root: docker build -f backend/Dockerfile .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Repo layout: /app/backend, /app/data
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY data /app/data

WORKDIR /app/backend

EXPOSE 8000
CMD ["python", "app.py"]
