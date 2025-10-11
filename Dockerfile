FROM python:3.10-slim

WORKDIR /opt/render/project/src

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxrender-dev \
    libxext6 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy your source code first!
COPY . .

# NOW clone YOLOX repo into the working directory
RUN git clone https://github.com/Megvii-BaseDetection/YOLOX.git yolox

# Install YOLOX requirements
RUN pip install -r yolox/requirements.txt

# Install YOLOX as editable package
RUN pip install -e yolox

# Install your requirements
RUN pip install -r requirements.txt

# Download YOLOX nano weights if not present
RUN if [ ! -f yolox_nano.pth ]; then \
    curl -L -o yolox_nano.pth https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1/yolox_nano.pth; \
    fi

EXPOSE 10000

ENV PYTHONPATH="${PYTHONPATH}:/opt/render/project/src/yolox"

CMD ["python", "app.py"]
