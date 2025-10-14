FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Download YOLOX weights (if needed)
RUN mkdir -p models

EXPOSE 8080

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# CRITICAL FIX: Use correct filename
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
