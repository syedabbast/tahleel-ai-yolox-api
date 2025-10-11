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

# Clone YOLOX repo and install as package
RUN git clone https://github.com/Megvii-BaseDetection/YOLOX.git yolox
RUN pip install -r yolox/requirements.txt
RUN pip install -e yolox

# Copy your API files
COPY requirements.txt .
COPY app.py .

RUN pip install -r requirements.txt

# Download yolox_nano.pth weights if needed
RUN curl -L -o yolox_nano.pth https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1/yolox_nano.pth

EXPOSE 10000
CMD ["python", "app.py"]
