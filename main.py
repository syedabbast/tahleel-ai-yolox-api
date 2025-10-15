"""
TAHLEEL.ai API - Phase 5: Claude AI Tactical Analysis
October 15, 2025 - COMPLETE PIPELINE
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
        "service": "TAHLEEL.ai API - COMPLETE",
        "version": "1.0.0",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "features": {
            "upload": "ready",
            "frame_extraction": "ready",
            "yolox_detection": "ready",
            "tactical_analysis": "ready",
            "claude_ai": "ready"
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
    """COMPLETE PIPELINE: Upload → Frames → Detection → Tactical Analysis"""
    try:
        from utils.cloud_storage import upload_video_to_gcs, upload_json_to_gcs
        from components.frame_extractor import extract_frames
        from components.yolox_detector import run_yolox_detection
        from components.tactical_processor import process_tactical_analysis
        
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
        
        # Step 4: TACTICAL ANALYSIS with Claude AI
        tactical_report = process_tactical_analysis(video_id, detections, metadata)
        
        # Save complete analysis to GCS
        upload_json_to_gcs(tactical_report, f"{video_id}-tactical-report")
        upload_json_to_gcs(
            {"detections": detections, "metadata": metadata},
            f"{video_id}-detections"
        )
        
        # Return complete analysis
        return JSONResponse(content={
            **tactical_report,
            "gcs_url": gcs_url,
            "storage": {
                "video_url": gcs_url,
                "frames_folder": f"gs://tahleel-ai-videos/frames/{video_id}/",
                "tactical_report": f"gs://tahleel-ai-videos/results/{video_id}-tactical-report.json",
                "detections_json": f"gs://tahleel-ai-videos/results/{video_id}-detections.json"
            },
            "message": "Complete tactical analysis ready for coach!",
            "ready_for": "Arab League presentation"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results/{video_id}")
def get_results(video_id: str):
    """Get tactical analysis results"""
    try:
        from utils.cloud_storage import get_analysis_result_from_gcs
        
        # Get tactical report
        tactical_report = get_analysis_result_from_gcs(f"{video_id}-tactical-report")
        
        if tactical_report:
            return JSONResponse(content={
                "status": "complete",
                "video_id": video_id,
                "data": tactical_report,
                "message": "Tactical analysis complete"
            })
        else:
            return JSONResponse(content={
                "status": "not_found",
                "video_id": video_id,
                "message": "Analysis not found"
            })
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
