FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for YOLOX
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Install PyTorch (CPU version - lighter and faster to build)
RUN pip install --no-cache-dir \
    torch==2.1.2+cpu \
    torchvision==0.16.2+cpu \
    -f https://download.pytorch.org/whl/torch_stable.html

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install YOLOX (without building from source)
RUN pip install --no-cache-dir yolox==0.3.0 --no-deps

# Copy application
COPY . .

# Create directories
RUN mkdir -p models frames

# Download YOLOX nano weights
RUN wget -q https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_nano.pth \
    -O models/yolox_nano.pth || echo "Will download at runtime"

EXPOSE 8080

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

CMD uvicorn main:app --host 0.0.0.0 --port $PORT
