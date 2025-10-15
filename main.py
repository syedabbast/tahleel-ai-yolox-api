"""
TAHLEEL.ai API - Phase 3.5: Return Full Detection Data
October 15, 2025
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
        "service": "TAHLEEL.ai API - Phase 3.5",
        "version": "1.0.0",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "features": {
            "upload": "ready",
            "frame_extraction": "ready",
            "yolox_detection": "ready",
            "full_detections": "ready"
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
    """Full pipeline: Upload → Extract Frames → YOLOX Detection → Return ALL data"""
    try:
        from utils.cloud_storage import upload_video_to_gcs, upload_json_to_gcs
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
        
        # Build complete response with FULL detection data
        analysis_result = {
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
            "detections": detections[:10],  # First 10 frames (full data too large for response)
            "message": "Video analysis complete with full detection data!",
            "storage": {
                "video_url": gcs_url,
                "frames_folder": f"gs://tahleel-ai-videos/frames/{video_id}/",
                "detections_json": f"gs://tahleel-ai-videos/results/{video_id}-detections.json"
            },
            "next_step": "Claude AI tactical analysis"
        }
        
        # Save full detections to GCS for Claude AI to read
        upload_json_to_gcs(
            {"detections": detections, "metadata": metadata},
            f"{video_id}-detections"
        )
        
        return JSONResponse(content=analysis_result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results/{video_id}")
def get_results(video_id: str):
    """Get full analysis results from GCS"""
    try:
        from utils.cloud_storage import get_analysis_result_from_gcs
        
        # Try to get detections
        detections_data = get_analysis_result_from_gcs(f"{video_id}-detections")
        
        if detections_data:
            return JSONResponse(content={
                "status": "complete",
                "video_id": video_id,
                "data": detections_data,
                "message": "Full detection data available"
            })
        else:
            return JSONResponse(content={
                "status": "not_found",
                "video_id": video_id,
                "message": "Analysis not found or still processing"
            })
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
