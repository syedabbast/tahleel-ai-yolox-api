# TAHLEEL.ai YOLOX Tactical Analysis API - Dockerfile
# Production-ready container for FastAPI backend (NO MOCK DATA)

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN pip install --upgrade pip && \
    pip install torch==2.1.2 && \
    pip install fastapi==0.109.0 uvicorn[standard]==0.27.0 python-multipart==0.0.6 opencv-python==4.9.0.80 numpy==1.24.3 scikit-learn==1.3.2 pandas==2.1.4 scipy==1.11.4 google-cloud-storage==2.14.0 Pillow==10.2.0 motpy==0.0.10 pytest==7.4.3 httpx==0.25.2 && \
    pip install yolox==0.3.0

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
