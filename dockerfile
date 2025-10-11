FROM python:3.10-slim

WORKDIR /app

# System dependencies for YOLOX and OpenCV
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxrender-dev \
    libxext6 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Clone YOLOX repo and install as Python package
RUN git clone https://github.com/Megvii-BaseDetection/YOLOX.git /app/yolox
RUN pip install -r /app/yolox/requirements.txt
RUN pip install -e /app/yolox

# Copy your API files (AFTER YOLOX install to avoid path issues)
COPY requirements.txt .
COPY app.py .

RUN pip install -r requirements.txt

# Download YOLOX nano weights if not present
RUN if [ ! -f yolox_nano.pth ]; then \
    curl -L -o yolox_nano.pth https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1/yolox_nano.pth; \
    fi

EXPOSE 10000

CMD ["python", "app.py"]
