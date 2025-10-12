"""
TAHLEEL.ai YOLOX Tactical Analysis API - FastAPI Entrypoint

Purpose:
- Accepts football match video uploads (multipart/form-data)
- Validates video (format, length, size)
- Extracts frames at 5 FPS
- Runs YOLOX-S detection, separates teams by jersey color, tracks players
- Processes tactical analysis (formations, weaknesses, movement)
- Uploads video, frames, results to Google Cloud Storage
- Returns enriched tactical JSON for Claude AI & frontend
- Health check and result retrieval endpoints

Business context: Arab League coaches, $15K-$45K/month, NO mock data
"""

import os
import uuid
import time
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from utils.validators import validate_video_file
from utils.cloud_storage import (
    upload_video_to_gcs,
    upload_json_to_gcs,
    get_analysis_result_from_gcs
)
from components.frame_extractor import extract_frames
from components.yolox_detector import run_yolox_detection
from components.tactical_processor import process_tactical_analysis

# ---- FastAPI setup ----
app = FastAPI(
    title="TAHLEEL.ai YOLOX Football Tactical Analysis API",
    description="Production-grade API for real match analysis (no mock data)",
    version="1.0.0"
)

# CORS: Allow frontend calls
origins = [
    "http://localhost:3000",
    "https://tahleel.netlify.app"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- AUTHENTICATION (API Key/Bearer) ----
def verify_auth(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid API token")
    # TODO: Validate token with Supabase or internal logic
    return authorization.split(" ")[1]

# ---- ENDPOINT: HEALTH CHECK ----
@app.get("/health", tags=["System"])
def health():
    return {
        "status": "healthy",
        "service": "TAHLEEL.ai YOLOX Tactical Analysis API",
        "model": "YOLOX-S",
        "cloud_storage": "gs://tahleel-ai-videos",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

# ---- ENDPOINT: ANALYZE (VIDEO UPLOAD & TACTICAL ANALYSIS) ----
@app.post("/analyze", tags=["Analysis"])
async def analyze_video(
    video_file: UploadFile = File(...),
    authorization: str = Depends(verify_auth)
):
    # --- Validate video ---
    try:
        validate_video_file(video_file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # --- Save video to GCS ---
    video_id = str(uuid.uuid4())
    gcs_video_url = await upload_video_to_gcs(video_file, video_id)
    if not gcs_video_url:
        raise HTTPException(status_code=500, detail="Failed to upload video to cloud storage")

    # --- Extract frames at 5 FPS ---
    frames, metadata = extract_frames(gcs_video_url, fps=5, resize=(1280, 720))
    if not frames or metadata["total_frames"] == 0:
        raise HTTPException(status_code=500, detail="Failed to extract frames from video")

    # --- YOLOX detection & team separation ---
    detections = run_yolox_detection(frames)
    if not detections or len(detections) == 0:
        raise HTTPException(status_code=500, detail="YOLOX detection failed or returned no results")

    # --- Tactical processing ---
    tactical_json = process_tactical_analysis(video_id, detections, metadata)
    if not tactical_json or tactical_json.get("status") != "success":
        raise HTTPException(status_code=500, detail="Tactical analysis failed")

    # --- Upload results JSON to GCS ---
    json_url = upload_json_to_gcs(tactical_json, video_id)
    if not json_url:
        raise HTTPException(status_code=500, detail="Failed to upload analysis JSON to cloud storage")

    # --- Return result JSON (Claude-compatible) ---
    tactical_json["storage"]["json_url"] = json_url
    tactical_json["storage"]["video_url"] = gcs_video_url

    return JSONResponse(content=tactical_json)

# ---- ENDPOINT: GET RESULTS (BY video_id) ----
@app.get("/results/{video_id}", tags=["Analysis"])
def get_analysis(video_id: str, authorization: str = Depends(verify_auth)):
    result_json = get_analysis_result_from_gcs(video_id)
    if not result_json:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    return JSONResponse(content=result_json)
