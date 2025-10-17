FROM python:3.9-slim

WORKDIR /app

# Install system dependencies (FIXED package names)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install YOLOx from PyPI
RUN pip install --no-cache-dir yolox==0.3.0

COPY . .

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
