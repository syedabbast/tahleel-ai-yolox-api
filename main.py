"""
TAHLEEL.ai API - Phase 1: Upload + Frame Extraction
October 14, 2025 - YOLOX integration in progress
"""

import os
import uuid
import time
from fastapi import FastAPI, File, UploadFile, HTTPException
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

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "TAHLEEL.ai API - Phase 1",
        "version": "1.0.0",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "features": {
            "upload": "ready",
            "frame_extraction": "ready",
            "yolox": "deploying"
        }
    }

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
            "message": "Video uploaded - frame extraction ready",
            "status": "uploaded"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_video(video: UploadFile = File(...)):
    """Upload and extract frames (YOLOX coming next)"""
    try:
        from utils.cloud_storage import upload_video_to_gcs
        from components.frame_extractor import extract_frames
        
        video_id = str(uuid.uuid4())
        
        # Upload video
        gcs_url = await upload_video_to_gcs(video, video_id)
        if not gcs_url:
            raise HTTPException(status_code=500, detail="Upload failed")
        
        # Extract frames
        frames, metadata = extract_frames(gcs_url, fps=5, resize=(1280, 720))
        
        return JSONResponse(content={
            "status": "success",
            "video_id": video_id,
            "gcs_url": gcs_url,
            "frames_extracted": len(frames),
            "metadata": metadata,
            "message": "Frames extracted - YOLOX processing next",
            "next_step": "YOLOX detection"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results/{video_id}")
def get_results(video_id: str):
    return JSONResponse(content={
        "status": "processing",
        "video_id": video_id,
        "message": "YOLOX integration in progress"
    })
