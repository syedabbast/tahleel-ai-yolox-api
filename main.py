"""
TAHLEEL.ai YOLOX Tactical Analysis API - FastAPI Production
August 12, 2025 - Arab League Launch Version
"""

import os
import uuid
import time
from fastapi import FastAPI, File, UploadFile, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from components.frame_extractor import extract_frames
from components.yolox_detector import run_yolox_detection
from components.tactical_processor import process_tactical_analysis

# ---- FastAPI setup ----
app = FastAPI(title="TAHLEEL.ai API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Auth ----
def verify_auth(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing API token")
    return True

# ---- Health ----
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "TAHLEEL.ai",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

# ---- Analyze ----
@app.post("/analyze")
async def analyze_video(
    video: UploadFile = File(...),
    auth: bool = Header(default=False, alias="Authorization")
):
    start_time = time.time()
    
    # Save video temporarily
    video_id = str(uuid.uuid4())
    temp_path = f"/tmp/{video_id}.mp4"
    
    with open(temp_path, "wb") as f:
        content = await video.read()
        f.write(content)
    
    # Extract frames
    frames, metadata = extract_frames(f"file://{temp_path}", fps=5, resize=(1280, 720))
    
    # YOLOX detection
    detections = run_yolox_detection(frames)
    
    # Tactical analysis
    metadata["processing_time"] = int(time.time() - start_time)
    tactical_json = process_tactical_analysis(video_id, detections, metadata)
    
    # Cleanup
    os.remove(temp_path)
    
    return JSONResponse(content=tactical_json)

# ---- Get Results ----
@app.get("/results/{video_id}")
def get_results(video_id: str):
    from utils.cloud_storage import get_analysis_result_from_gcs
    result = get_analysis_result_from_gcs(video_id)
    if not result:
        raise HTTPException(status_code=404, detail="Not found")
    return JSONResponse(content=result)
