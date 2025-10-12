# TAHLEEL.ai GCP Cloud Run Backend

**Project:** tahleel-ai-video-analysis  
**Owner:** Syed (Auwire Technologies)  
**Purpose:** Production-ready Python backend for tactical video analysis (GPT Vision, YOLOX, Claude AI) on GCP  
**Critical:** No mock data—REAL video, REAL analysis, REAL business value

---

## 🚀 Quick Start

### 1. **Prepare Your Repo**

Copy these files into your backend folder:
- `Dockerfile`
- `requirements.txt`
- `app.py`
- `gcs_helper.py`
- `.env.example` (copy as `.env` and fill secrets)

---

### 2. **Setup GCP Project & Bucket**

- **Project:** `tahleel-ai-video-analysis`  
- **Bucket:** `tahleel-ai-videos` (already created, see Image 1)

If you need a service account:
- Go to IAM & Admin → Service Accounts
- Create a new account with "Storage Object Admin" role
- Download the JSON key file (use for local dev only)

---

### 3. **GCP Console UI Deployment (No CLI needed)**

#### **A. Build and Deploy Container**

1. Go to [Cloud Run](https://console.cloud.google.com/run) in your GCP project.
2. Click **"Create Service"**.
3. Choose **"Deploy one revision from source"** → Select "Container" → "Upload source code".
4. Upload your backend folder with all files.
5. Set the service name: `tahleel-ai-backend`
6. Set region: `us-central1`
7. Set **port to 8080** (default for Cloud Run).
8. Set environment variables from `.env` (GCS bucket, model paths, API keys).
9. Click **"Deploy"**.

---

#### **B. Configure Permissions**

- Allow **unauthenticated invocations** for public API
- If using service account, attach it in the Cloud Run service settings

---

### 4. **Testing Endpoints**

- Get the HTTPS endpoint from Cloud Run console (e.g., `https://tahleel-ai-backend-xxxxx.a.run.app`)
- Test `/health` endpoint:
  ```bash
  curl https://tahleel-ai-backend-xxxxx.a.run.app/health
  ```
- Test `/upload` and `/analyze` with Postman or frontend

---

### 5. **Integrate with Node.js Backend**

- Update your Node API orchestration endpoint to call the new Cloud Run URL for analysis.
- Use GCS URLs for video uploads/processing.

---

### 6. **Production Notes**

- **No mock data**—all endpoints run real analysis.
- **Analysis results** should be stored in Supabase as per business workflow.
- **Security:** Use JWT, CORS, and GCS IAM for production.
- **Performance:** Target ≤5 min per video, ≥80% formation accuracy.

---

## 📂 File Structure

```
/
├── Dockerfile
├── requirements.txt
├── app.py
├── gcs_helper.py
├── .env.example
```

Structure
tahleel-ai-yolox-api/
├── main.py                      # FastAPI entry point, defines API endpoints
├── requirements.txt             # Python dependencies (see previous code)
├── Dockerfile                   # Containerization for Cloud Run/Render
├── .dockerignore                # Ignore files for Docker build
├── .gitignore                   # Git ignore file
├── README.md                    # Documentation, setup, API usage
│
├── components/                  # Core business logic modules
│   ├── __init__.py
│   ├── frame_extractor.py       # Frame extraction: OpenCV, GCS upload
│   ├── yolox_detector.py        # YOLOX-S detection, team color clustering, tracking
│   └── tactical_processor.py    # Converts detection to tactical JSON
│
├── models/
│   └── download_weights.py      # Downloads YOLOX-S weights for inference
│
├── utils/                       # Utility modules
│   ├── __init__.py
│   ├── cloud_storage.py         # GCS integration: upload/download files
│   └── validators.py            # Video validation: format, length, size
│
├── tests/                       # Automated test suite
│   └── test_api.py              # API endpoint tests (pytest)
│
└── .env.example                 # Example environment variables (GCS, API keys, etc.)


---

## 🏆 Critical Standards

- **Business Value:** All code delivers tactical advantage for Arab League teams.
- **Reliability:** 99% uptime, 5-min analysis speed.
- **Scalability:** Supports multiple coaches, 10TB+ video storage.
- **Security:** Role-based access, JWT, no public exposure of sensitive data.

---

## 🚨 Support

- Email: support@tahleel.ai
- Docs: https://docs.tahleel.ai
- Owner: Syed (Auwire Technologies)

---

## ❗ Final Reminder

**NO MOCK DATA.  
NO PROTOTYPES.  
REAL AI, REAL ANALYSIS, REAL BUSINESS VALUE.  
LAUNCH-READY FOR ARAB LEAGUE.**
