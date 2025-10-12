# TAHLEEL.ai YOLOX Tactical Analysis API

**Production-Ready FastAPI Backend for Arab League Tactical Analysis — NO MOCK DATA**

---

## Overview

TAHLEEL.ai is an enterprise-grade football tactical analysis platform for Arab League teams, providing **real-time match video analysis** using YOLOX-S, Google Cloud Storage, and Claude AI. This backend processes real match videos, extracts frames, detects players/formations, and generates actionable tactical insights in ≤5 minutes.

**Business Context:**  
- Real Arab League coaches ($15K-$45K/month)  
- 99% uptime, ≤5 min analysis, ≥80% formation accuracy  
- No mock data – only real video, real analysis

---

## Features

- **FastAPI API** — `/analyze`, `/health`, `/results/{video_id}`
- **Video upload & validation** (format, size, duration)
- **Frame extraction** (OpenCV, 5 FPS, 1280x720)
- **YOLOX-S detection** (players, ball, team color clustering, tracking)
- **Tactical JSON generation** (formations, weaknesses, recommendations)
- **Dual save** — Results to **Google Cloud Storage** and **Supabase**
- **Enterprise error handling & security**
- **Automated testing** (pytest, httpx)
- **Production-ready Dockerfile**

---

## Architecture

```
React Frontend (Netlify) → FastAPI Backend (Render/Cloud Run)
   |
   → GCS (video, frames, results)
   → Supabase (analysis results, user base)
   → Claude AI (tactical insights)
```

---

## Setup

### 1. Clone Repo

```bash
git clone https://github.com/your-org/tahleel-ai-yolox-api.git
cd tahleel-ai-yolox-api
```

### 2. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create `.env` file or use GCP default credentials.

```env
GCS_BUCKET=tahleel-ai-videos
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

### 4. Download YOLOX-S Weights

Place `yolox_s.pth` in `models/` or run:

```bash
python models/download_weights.py
```

### 5. Run FastAPI Locally

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## Docker Deployment

### Build & Run

```bash
docker build -t tahleel-ai-yolox-api .
docker run --env-file .env -p 8000:8000 tahleel-ai-yolox-api
```

### Cloud Run/Render

- Configure build command: `docker build ...`
- Set environment variables in dashboard
- Expose port 8000

---

## API Reference

### POST `/analyze`  
Upload and analyze video.  
**Request:** `multipart/form-data` (field: `video_file`), Bearer token required.

**Response:**  
```json
{
  "status": "success",
  "video_id": "...",
  "teams": {...},
  "tactical_analysis": {...},
  "player_analysis": [...],
  "team_metrics": {...},
  "key_moments": [...],
  "recommendations": {...},
  "storage": {
    "video_url": "...",
    "json_url": "...",
    "annotated_frames": [...]
  }
}
```

### GET `/health`  
Returns service/model/storage status.

### GET `/results/{video_id}`  
Returns stored tactical analysis JSON.

---

## Testing

```bash
pytest tests/
```

---

## Folder Structure

```
tahleel-ai-yolox-api/
├── main.py
├── requirements.txt
├── Dockerfile
├── components/
│   ├── frame_extractor.py
│   ├── yolox_detector.py
│   └── tactical_processor.py
├── models/
│   └── download_weights.py
├── utils/
│   ├── cloud_storage.py
│   ├── supabase.py
│   └── validators.py
├── tests/
│   └── test_api.py
├── .env.example
└── README.md
```

---

## Notes

- **NO MOCK DATA** — All endpoints use real video, real analysis.
- **Dual Save** — Results stored in both GCS and Supabase for reliability.
- **For business launch:** 5-minute analysis, 99% uptime, enterprise security.
- **Frontend:** React calls API via HTTPS, JWT required.

---

## Support

For help, contact Syed (Auwire Technologies):  
**Email:** support@tahleel.ai  
**Docs:** https://docs.tahleel.ai

---
