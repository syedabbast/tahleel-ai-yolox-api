# TAHLEEL.ai Backend - GCP Cloud Run Dockerfile
# Project: tahleel-ai-video-analysis

FROM python:3.10-slim

WORKDIR /app

# System dependencies for YOLOX, OpenCV, Pillow
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxrender-dev \
    libxext6 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Clone YOLOX repo into /app/yolox
RUN git clone https://github.com/Megvii-BaseDetection/YOLOX.git yolox

# Install YOLOX requirements and package
RUN pip install -r yolox/requirements.txt
RUN pip install -e yolox

# Copy your API files
COPY requirements.txt .
COPY app.py .
COPY gcs_helper.py .

# Install API dependencies
RUN pip install -r requirements.txt

# Download YOLOX-nano weights (overwrite if needed)
RUN curl -L -o yolox_nano.pth https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1/yolox_nano.pth

EXPOSE 8080

CMD ["python", "app.py"]
