# backend/Dockerfile

FROM python:3.10-slim

# Installa librerie di sistema per MariaDB
RUN apt-get update && apt-get install -y \
    mariadb-client \
    libmariadb-dev \
    gcc \
    && apt-get clean

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src /app/src
WORKDIR /app/src

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "backend.backend:app", "--host", "0.0.0.0", "--port", "8000"]
