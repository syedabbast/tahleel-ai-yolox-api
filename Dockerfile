# TAHLEEL.ai YOLOX Tactical Analysis API - Dockerfile
# Production-ready container for FastAPI backend (NO MOCK DATA)

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (build tools, ffmpeg, OpenCV dependencies)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        ffmpeg \
        libsm6 \
        libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Install torch first for yolox compilation
RUN pip install torch==2.1.2 --no-cache-dir

# Install all other Python dependencies in one step (except yolox)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install yolox after torch is present (also in requirements.txt for clarity, but safe to repeat)
RUN pip install yolox==0.3.0 --no-cache-dir

# Copy the full source code into the container
COPY . .

# Download YOLOX-S weights if not present (ignore error if script missing)
RUN mkdir -p models && \
    (python models/download_weights.py || true)

# Expose FastAPI port
EXPOSE 8000

# Set environment variables for GCS/Supabase if needed
ENV PYTHONUNBUFFERED=1

# Run FastAPI app
CMD ["uvicorn", "mian:app", "--host", "0.0.0.0", "--port", "8000"]
