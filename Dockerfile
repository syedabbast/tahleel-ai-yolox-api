FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for YOLOX (ADD CMAKE)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    build-essential \
    cmake \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Install PyTorch CPU version (OFFICIAL METHOD)
RUN pip install --no-cache-dir \
    torch==2.1.2 \
    torchvision==0.16.2 \
    torchaudio==2.1.2 \
    --index-url https://download.pytorch.org/whl/cpu

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p models frames

# YOLOx-M weights downloaded at runtime from GCS

EXPOSE 8080

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

CMD uvicorn main:app --host 0.0.0.0 --port $PORT
