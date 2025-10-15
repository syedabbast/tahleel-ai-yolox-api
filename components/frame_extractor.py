"""
Frame Extraction Module - TAHLEEL.ai
Extract frames from uploaded videos at 5 FPS
"""

import cv2
import numpy as np
import os
from google.cloud import storage
from tempfile import NamedTemporaryFile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GCS_BUCKET = os.getenv("GCS_BUCKET_NAME", "tahleel-ai-videos")

def download_video_from_gcs(gcs_url):
    """Download video from GCS to temp file"""
    try:
        logger.info(f"📥 Downloading video from {gcs_url}")
        
        client = storage.Client()
        bucket_name = gcs_url.replace("gs://", "").split("/")[0]
        blob_path = "/".join(gcs_url.replace("gs://", "").split("/")[1:])
        
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        
        temp_file = NamedTemporaryFile(delete=False, suffix=".mp4")
        blob.download_to_filename(temp_file.name)
        
        logger.info(f"✅ Downloaded to {temp_file.name}")
        return temp_file.name
        
    except Exception as e:
        logger.error(f"❌ Download error: {e}")
        return None

def upload_frame_to_gcs(frame_data, video_id, frame_number):
    """Upload frame image to GCS"""
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET)
        
        frame_path = f"frames/{video_id}/frame_{frame_number:04d}.jpg"
        blob = bucket.blob(frame_path)
        
        # Encode frame as JPEG
        success, jpg_data = cv2.imencode('.jpg', frame_data, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        if not success:
            raise Exception("Frame encoding failed")
        
        blob.upload_from_string(jpg_data.tobytes(), content_type="image/jpeg")
        
        return f"gs://{GCS_BUCKET}/{frame_path}"
        
    except Exception as e:
        logger.error(f"❌ Frame upload error: {e}")
        return None

def extract_frames(gcs_video_url, fps=5, resize=(1280, 720)):
    """
    Extract frames from video at specified FPS
    Returns: (list of frame URLs, metadata dict)
    """
    
    logger.info(f"🎬 Starting frame extraction from {gcs_video_url}")
    
    # Download video
    local_video_path = download_video_from_gcs(gcs_video_url)
    if not local_video_path:
        return [], {"error": "Video download failed", "total_frames": 0}
    
    try:
        # Open video
        cap = cv2.VideoCapture(local_video_path)
        
        if not cap.isOpened():
            raise Exception("Could not open video file")
        
        # Get video properties
        original_fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_sec = total_video_frames / original_fps
        video_id = gcs_video_url.split("/")[-1].replace(".mp4", "")
        
        # Calculate frame interval
        frame_interval = int(original_fps / fps)
        expected_frames = int(duration_sec * fps)
        
        logger.info(f"📊 Video: {duration_sec:.1f}s, {original_fps:.1f} FPS, extracting at {fps} FPS")
        logger.info(f"📊 Expected frames: {expected_frames}")
        
        frame_urls = []
        frame_count = 0
        extracted_count = 0
        
        while cap.isOpened() and extracted_count < expected_frames:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            frame_count += 1
            
            # Extract frame at interval
            if frame_count % frame_interval == 0:
                # Resize frame
                frame_resized = cv2.resize(frame, resize)
                
                # Upload to GCS
                frame_url = upload_frame_to_gcs(frame_resized, video_id, extracted_count)
                
                if frame_url:
                    frame_urls.append(frame_url)
                    extracted_count += 1
                    
                    if extracted_count % 50 == 0:
                        logger.info(f"✅ Extracted {extracted_count}/{expected_frames} frames")
        
        cap.release()
        os.remove(local_video_path)
        
        metadata = {
            "duration_seconds": int(duration_sec),
            "original_fps": int(original_fps),
            "extraction_fps": fps,
            "total_frames": extracted_count,
            "video_resolution": f"{resize[0]}x{resize[1]}",
            "video_id": video_id
        }
        
        logger.info(f"🎉 Extraction complete! {extracted_count} frames saved to GCS")
        
        return frame_urls, metadata
        
    except Exception as e:
        logger.error(f"❌ Frame extraction error: {e}")
        if os.path.exists(local_video_path):
            os.remove(local_video_path)
        return [], {"error": str(e), "total_frames": 0}
