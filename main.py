"""
TAHLEEL.ai Basic API - October 14, 2025
Syed (Auwire Technologies)
Phase 1: File upload + GCS storage (YOLOX integration later)
"""

import os
import uuid
import time
from fastapi import FastAPI, File, UploadFile, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="TAHLEEL.ai API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "TAHLEEL.ai Basic API",
        "version": "1.0.0",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "message": "Ready for video uploads - YOLOX integration coming next"
    }

# Upload video
@app.post("/upload")
async def upload_video(video: UploadFile = File(...)):
    """Upload video to GCS"""
    try:
        from utils.cloud_storage import upload_video_to_gcs
        
        video_id = str(uuid.uuid4())
        gcs_url = await upload_video_to_gcs(video, video_id)
        
        if not gcs_url:
            raise HTTPException(status_code=500, detail="Upload failed")
        
        return JSONResponse(content={
            "success": True,
            "video_id": video_id,
            "gcs_url": gcs_url,
            "message": "Video uploaded successfully. Analysis will be available soon.",
            "status": "uploaded"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Analyze endpoint (placeholder for now)
@app.post("/analyze")
async def analyze_video(video: UploadFile = File(...)):
    """Accept video for analysis (YOLOX integration coming)"""
    try:
        from utils.cloud_storage import upload_video_to_gcs
        
        video_id = str(uuid.uuid4())
        gcs_url = await upload_video_to_gcs(video, video_id)
        
        # Placeholder response
        return JSONResponse(content={
            "status": "success",
            "video_id": video_id,
            "gcs_url": gcs_url,
            "message": "Video received. YOLOX processing will be integrated next.",
            "processing_status": "queued",
            "estimated_time": "5 minutes (once YOLOX integrated)"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get results
@app.get("/results/{video_id}")
def get_results(video_id: str):
    """Get analysis results"""
    return JSONResponse(content={
        "status": "processing",
        "video_id": video_id,
        "message": "YOLOX analysis integration coming next"
    })
