# TAHLEEL.ai YOLOX Tactical Analysis API - Dockerfile
# Production-ready container for FastAPI backend (NO MOCK DATA)

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        ffmpeg \
        libsm6 \
        libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy app code
COPY . .

# Download YOLOX-S weights (if not present)
RUN mkdir -p models && \
    python models/download_weights.py || true

# Expose FastAPI port
EXPOSE 8000

# Set environment variables for GCS/Supabase if needed
ENV PYTHONUNBUFFERED=1

# Run FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
