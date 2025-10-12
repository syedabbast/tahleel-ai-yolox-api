# TAHLEEL.ai Backend - GCP Cloud Run Dockerfile (Production Grade)
# Author: Syed (Auwire Technologies)

FROM python:3.10-slim

WORKDIR /app

# System dependencies for CV/AI
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

# Install YOLOX requirements & package
RUN pip install -r yolox/requirements.txt
RUN pip install -e yolox

# Copy API files
COPY requirements.txt .
COPY app.py .
COPY gcs_helper.py .

# Install API dependencies - CRITICAL: flask_cors and other dependencies for app.py
RUN pip install --no-cache-dir -r requirements.txt

# Download YOLOX-nano weights
RUN curl -L -o yolox_nano.pth https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1/yolox_nano.pth

EXPOSE 8080

# Use Gunicorn for production
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
