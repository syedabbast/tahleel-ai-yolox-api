"""
Frame Extraction Module - TAHLEEL.ai YOLOX Tactical Analysis

Purpose:
- Extract frames from uploaded football video at 5 FPS
- Resize frames to 1280x720 for efficiency
- Save extracted frames to Google Cloud Storage ("frames/" folder)
- Return frame list and video metadata for downstream YOLOX detection

Business context:
- Must be production-ready, real videos only (NO mock data)
- Enables ≤5 min full analysis for Arab League teams

Dependencies:
- OpenCV (cv2)
- numpy
- google-cloud-storage

Usage:
frames, metadata = extract_frames(gcs_video_url, fps=5, resize=(1280,720))
"""

import cv2
import numpy as np
import os
from google.cloud import storage
from tempfile import NamedTemporaryFile

# --- CONFIG ---
GCS_BUCKET = "tahleel-ai-videos"
FRAMES_FOLDER = "frames"

def download_video_from_gcs(gcs_url):
    """
    Download video file from GCS to local temp file.
    gcs_url: "gs://tahleel-ai-videos/videos/xxxx.mp4"
    Returns local file path.
    """
    try:
        client = storage.Client()
        bucket_name, blob_path = gcs_url.replace("gs://", "").split("/", 1)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        temp_file = NamedTemporaryFile(delete=False, suffix=".mp4")
        blob.download_to_filename(temp_file.name)
        return temp_file.name
    except Exception as e:
        print(f"❌ Error downloading video from GCS: {e}")
        return None

def upload_frame_to_gcs(np_image, video_id, frame_number):
    """
    Upload numpy image (BGR) to GCS frames folder.
    Returns GCS URL of uploaded frame.
    """
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET)
        frame_path = f"{FRAMES_FOLDER}/{video_id}/frame_{frame_number:04d}.jpg"
        blob = bucket.blob(frame_path)
        # Encode image as JPEG
        success, jpg_bytes = cv2.imencode('.jpg', np_image)
        if not success:
            raise Exception("Image encoding failed")
        blob.upload_from_string(jpg_bytes.tobytes(), content_type="image/jpeg")
        return f"gs://{GCS_BUCKET}/{frame_path}"
    except Exception as e:
        print(f"❌ Error uploading frame to GCS: {e}")
        return None

def extract_frames(gcs_video_url, fps=5, resize=(1280, 720)):
    """
    Extract frames from video at specified FPS, resize, upload to GCS.
    Returns tuple: (list of GCS frame URLs, metadata dict)
    """
    # --- Download video from GCS ---
    local_video_path = download_video_from_gcs(gcs_video_url)
    if not local_video_path:
        return [], {"error": "Video download failed", "total_frames": 0}

    try:
        cap = cv2.VideoCapture(local_video_path)
        original_fps = cap.get(cv2.CAP_PROP_FPS) or 30
        duration_sec = cap.get(cv2.CAP_PROP_FRAME_COUNT) / original_fps
        video_id = os.path.basename(local_video_path).replace(".mp4", "")
        frame_interval = int(original_fps / fps)
        total_frames = int(duration_sec * fps)

        frame_urls = []
        frame_count = 0
        extracted_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1

            # Sample frame at interval
            if frame_count % frame_interval == 0:
                # Resize frame
                frame_resized = cv2.resize(frame, resize)
                # Upload to GCS
                frame_url = upload_frame_to_gcs(frame_resized, video_id, extracted_count)
                if frame_url:
                    frame_urls.append(frame_url)
                extracted_count += 1

            # Stop if reached max frames
            if extracted_count >= total_frames:
                break

        cap.release()
        os.remove(local_video_path)  # Clean up temp file

        metadata = {
            "duration_seconds": int(duration_sec),
            "original_fps": int(original_fps),
            "extraction_fps": fps,
            "total_frames": extracted_count,
            "video_resolution": f"{resize[0]}x{resize[1]}"
        }

        print(f"✅ Extracted {extracted_count} frames from {local_video_path}")
        return frame_urls, metadata

    except Exception as e:
        print(f"❌ Frame extraction error: {e}")
        return [], {"error": str(e), "total_frames": 0}
