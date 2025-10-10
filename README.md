# TAHLEEL.ai YOLOX API Microservice

**Production-Ready YOLOX REST API for Football Video Analysis**  
_Auwire Technologies | Arab League Tactical Intelligence Platform_

---

## 🚀 Overview

This repository provides a **Flask-based REST API** for running YOLOX object detection on football match frames.  
It is designed to be deployed as a **microservice on Render** (or similar cloud platform) and integrated with the TAHLEEL.ai backend for real-time tactical analysis.

- **Detects:** Players, ball, kit colors, formation shape (with post-processing)
- **Endpoint:** `/detect` — Accepts image URL, returns detection results in JSON
- **Integration:** Node.js backend calls API for each extracted frame
- **Deployment:** Dockerfile included for cloud-native deployment

---

## 📦 File Structure

```
/
├── app.py                # Main Flask API application
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container build for Render/AWS/Cloud
├── README.md             # This documentation
└── yolox_s.pth           # YOLOX model weights (downloaded at build/run)
```

---

## 🔧 Setup & Installation

### 1. **Clone the Repository**

```bash
git clone https://github.com/your-org/tahleel-ai-yolox-api.git
cd tahleel-ai-yolox-api
```

### 2. **YOLOX Model Weights**

- **Download weights:**  
  Download `yolox_s.pth` from [YOLOX Official Releases](https://github.com/Megvii-BaseDetection/YOLOX/releases).
- **Place in repo root** (or see Dockerfile for auto-download).

### 3. **Install Python Dependencies**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. **Run Locally (for testing)**

```bash
python app.py
# API will run on http://localhost:10000
```

---

## 🚀 Deployment (Render Cloud)

### **Using Dockerfile**

1. **Push to GitHub**  
   Ensure `app.py`, `requirements.txt`, `Dockerfile` are in repo root.

2. **Connect Render Service**  
   Create a new **Web Service** on Render, select this GitHub repo.

3. **Configure:**
   - **Build Command:** _Not needed (Dockerfile handles build)_
   - **Start Command:** _Not needed (Dockerfile CMD used)_
   - **Environment:** Python 3.10+ (Dockerfile sets base)
   - **Port:** `10000`
   - **Model Weights:**  
     By default, weights are downloaded at build. For custom weights, upload manually or adjust Dockerfile.

---

## 🛡️ API Reference

### **POST /detect**

- **Description:** Run YOLOX detection on a football frame
- **Request:**
  ```json
  {
    "image_url": "https://your-public-frame-url.jpg"
  }
  ```
- **Response:**
  ```json
  {
    "success": true,
    "detections": [
      {
        "label": "person",
        "bbox": [x0, y0, x1, y1],
        "score": 0.97
      },
      {
        "label": "sports ball",
        "bbox": [x0, y0, x1, y1],
        "score": 0.83
      }
    ],
    "frame_url": "https://your-public-frame-url.jpg"
  }
  ```
- **Health Check:**  
  `GET /health` returns status and model info.

---

## ⚙️ Environment Variables (Optional)

- `YOLOX_WEIGHTS_URL` — Custom URL for weights download (if not using default)
- `PORT` — API server port (default: `10000`)

---

## 🏆 Production Tips

- **Do NOT commit large weights to GitHub.**  
  Use Dockerfile to download or upload via Render dashboard.
- **Ensure public image URLs.**  
  API cannot access private storage or local files.
- **Monitor logs on Render.**  
  For debugging and model inference errors.
- **Scale service:**  
  For heavy workloads, use GPU instance or autoscaling.

---

## 📄 License

Proprietary © 2025 Auwire Technologies — For use with TAHLEEL.ai only.

---

## 🛠️ Support

- [support@tahleel.ai](mailto:support@tahleel.ai)
- [docs.tahleel.ai](https://docs.tahleel.ai)

---

## 🔗 References

- [YOLOX GitHub](https://github.com/Megvii-BaseDetection/YOLOX)
- [TAHLEEL.ai Backend](https://github.com/your-org/tahleel-ai-engine-backend)
