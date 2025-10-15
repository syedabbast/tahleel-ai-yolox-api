"""
TAHLEEL.ai API - Phase 3: Frame Extraction + YOLOX Detection
October 14, 2025
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
        "service": "TAHLEEL.ai API - Phase 3",
        "version": "1.0.0",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "features": {
            "upload": "ready",
            "frame_extraction": "ready",
            "yolox_detection": "ready"
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
            "message": "Video uploaded successfully",
            "status": "uploaded"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_video(video: UploadFile = File(...)):
    """Full pipeline: Upload → Extract Frames → YOLOX Detection"""
    try:
        from utils.cloud_storage import upload_video_to_gcs
        from components.frame_extractor import extract_frames
        from components.yolox_detector import run_yolox_detection
        
        video_id = str(uuid.uuid4())
        
        # Step 1: Upload video
        gcs_url = await upload_video_to_gcs(video, video_id)
        if not gcs_url:
            raise HTTPException(status_code=500, detail="Upload failed")
        
        # Step 2: Extract frames
        frames, metadata = extract_frames(gcs_url, fps=5, resize=(1280, 720))
        
        if not frames:
            raise HTTPException(status_code=500, detail="Frame extraction failed")
        
        # Step 3: Run YOLOX detection
        detections = run_yolox_detection(frames)
        
        # Calculate stats
        total_players_detected = sum(
            len(d['player_detections']) for d in detections
        )
        
        return JSONResponse(content={
            "status": "success",
            "video_id": video_id,
            "gcs_url": gcs_url,
            "frames_extracted": len(frames),
            "frames_analyzed": len(detections),
            "total_players_detected": total_players_detected,
            "metadata": metadata,
            "detections_summary": {
                "frames_processed": len(detections),
                "avg_players_per_frame": total_players_detected / len(detections) if detections else 0
            },
            "message": "Video analysis complete!",
            "next_step": "Claude AI tactical analysis"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results/{video_id}")
def get_results(video_id: str):
    return JSONResponse(content={
        "status": "complete",
        "video_id": video_id,
        "message": "Analysis pipeline ready for Claude AI"
    })
