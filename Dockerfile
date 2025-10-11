FROM python:3.10-slim

# Set working directory to Render's default build context
WORKDIR /opt/render/project/src

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxrender-dev \
    libxext6 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Clone YOLOX repo IN the working directory
RUN git clone https://github.com/Megvii-BaseDetection/YOLOX.git yolox

# Install YOLOX and its requirements
RUN pip install -r yolox/requirements.txt
RUN pip install -e yolox

# Copy your API files to the SAME directory (do NOT overwrite yolox folder)
COPY requirements.txt .
COPY app.py .

RUN pip install -r requirements.txt

# Download YOLOX nano weights if not present
RUN if [ ! -f yolox_nano.pth ]; then \
    curl -L -o yolox_nano.pth https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1/yolox_nano.pth; \
    fi

EXPOSE 10000

# Set PYTHONPATH so Render can find yolox
ENV PYTHONPATH="${PYTHONPATH}:/opt/render/project/src/yolox"

CMD ["python", "app.py"]
