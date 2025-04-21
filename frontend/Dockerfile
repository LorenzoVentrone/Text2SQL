# frontend/Dockerfile

FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src /app/src
COPY templates /app/templates

WORKDIR /app/src

ENV PYTHONPATH=/app/src

CMD ["uvicorn", "frontend.frontend:app", "--host", "0.0.0.0", "--port", "8001"]
