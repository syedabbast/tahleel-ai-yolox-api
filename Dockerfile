FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        ffmpeg \
        libsm6 \
        libxext6 \
        cmake \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

RUN pip install torch==2.1.2 --no-cache-dir

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install yolox==0.3.0 --no-cache-dir

COPY . .

RUN mkdir -p models && \
    (python models/download_weights.py || true)

EXPOSE 8000
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "mian:app", "--host", "0.0.0.0", "--port", "8000"]
