# Use base Python image
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies + build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Clone YOLOx repo (don't install, just use source)
RUN git clone https://github.com/Megvii-BaseDetection/YOLOX.git /yolox && \
    cd /yolox && \
    git checkout 0.3.0

# Add YOLOx to Python path (use without installing)
ENV PYTHONPATH="${PYTHONPATH}:/yolox"

COPY . .

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
