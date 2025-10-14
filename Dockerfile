FROM python:3.9-slim

WORKDIR /app

# Install ALL system dependencies (including cmake for ONNX)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    build-essential \
    cmake \
    protobuf-compiler \
    libprotobuf-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Install PyTorch FIRST
RUN pip install --no-cache-dir \
    torch==2.1.2 \
    torchvision==0.16.2

# Copy requirements
COPY requirements.txt .

# Install remaining packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Create models directory
RUN mkdir -p models

EXPOSE 8080
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

CMD uvicorn main:app --host 0.0.0.0 --port $PORT
