# TAHLEEL.ai YOLOX API Dockerfile
# Production-ready for Render (Python 3.10+, Flask, YOLOX, auto-download weights)

FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for YOLOX
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxrender-dev \
    libxext6 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and app files
COPY requirements.txt .
COPY app.py .

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Download YOLOX weights (yolox_s.pth) if not present
RUN if [ ! -f yolox_s.pth ]; then \
    curl -L -o yolox_s.pth https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1/yolox_s.pth; \
    fi

# Optional: Download YOLOX repo (for custom modules, if needed)
# RUN git clone https://github.com/Megvii-BaseDetection/YOLOX.git /app/YOLOX

# Set environment variable for Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=10000

# Expose API port
EXPOSE 10000

# Start Flask app
CMD ["python", "app.py"]
