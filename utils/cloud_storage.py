"""
Google Cloud Storage Utility - TAHLEEL.ai Tactical Analysis

Purpose:
- Upload videos, frames, and results JSON to Google Cloud Storage (GCS)
- Download frames/videos for analysis pipeline
- Generate GCS URLs for storage and retrieval
- Enterprise-grade: used for all backend storage, enables frontend and Claude AI downstream

Business context:
- NO MOCK DATA: Only real uploads and downloads
- Dual save: Results also stored in Supabase via utils/supabase.py

Dependencies:
- google-cloud-storage
"""

import os
from google.cloud import storage

GCS_BUCKET = "tahleel-ai-videos"
VIDEO_FOLDER = "videos"
FRAMES_FOLDER = "frames"
RESULTS_FOLDER = "results"

def get_gcs_client():
    """Initialize GCS client from service account or default credentials."""
    return storage.Client()

def upload_video_to_gcs(video_file, video_id):
    """
    Uploads video file to GCS /videos/ folder.
    Returns GCS URL.
    """
    try:
        client = get_gcs_client()
        bucket = client.bucket(GCS_BUCKET)
        ext = os.path.splitext(video_file.filename)[-1] or ".mp4"
        blob_path = f"{VIDEO_FOLDER}/{video_id}{ext}"
        blob = bucket.blob(blob_path)
        video_file.file.seek(0)
        blob.upload_from_file(video_file.file, content_type=video_file.content_type)
        return f"gs://{GCS_BUCKET}/{blob_path}"
    except Exception as e:
        print(f"❌ Error uploading video: {e}")
        return None

def upload_json_to_gcs(json_data, video_id):
    """
    Uploads tactical JSON result to GCS /results/ folder.
    Returns GCS URL.
    """
    import json
    try:
        client = get_gcs_client()
        bucket = client.bucket(GCS_BUCKET)
        json_path = f"{RESULTS_FOLDER}/{video_id}.json"
        blob = bucket.blob(json_path)
        blob.upload_from_string(json.dumps(json_data), content_type="application/json")
        return f"gs://{GCS_BUCKET}/{json_path}"
    except Exception as e:
        print(f"❌ Error uploading JSON: {e}")
        return None

def get_analysis_result_from_gcs(video_id):
    """
    Downloads tactical analysis result JSON from GCS.
    Returns parsed dict.
    """
    import json
    try:
        client = get_gcs_client()
        bucket = client.bucket(GCS_BUCKET)
        json_path = f"{RESULTS_FOLDER}/{video_id}.json"
        blob = bucket.blob(json_path)
        contents = blob.download_as_string()
        return json.loads(contents)
    except Exception as e:
        print(f"❌ Error downloading analysis JSON: {e}")
        return None

def upload_frame_to_gcs(np_image, video_id, frame_number):
    """
    Upload numpy image (BGR) to GCS frames folder.
    Returns GCS URL of uploaded frame.
    """
    import cv2
    try:
        client = get_gcs_client()
        bucket = client.bucket(GCS_BUCKET)
        frame_path = f"{FRAMES_FOLDER}/{video_id}/frame_{frame_number:04d}.jpg"
        blob = bucket.blob(frame_path)
        success, jpg_bytes = cv2.imencode('.jpg', np_image)
        if not success:
            raise Exception("Image encoding failed")
        blob.upload_from_string(jpg_bytes.tobytes(), content_type="image/jpeg")
        return f"gs://{GCS_BUCKET}/{frame_path}"
    except Exception as e:
        print(f"❌ Error uploading frame: {e}")
        return None

def download_frame_from_gcs(frame_url):
    """
    Download frame image from GCS URL.
    Returns numpy array (OpenCV BGR).
    """
    import tempfile
    import cv2
    try:
        if frame_url.startswith('gs://'):
            client = get_gcs_client()
            bucket_name, blob_path = frame_url.replace('gs://', '').split('/', 1)
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                blob.download_to_filename(tmp.name)
                frame = cv2.imread(tmp.name)
                return frame
        else:
            frame = cv2.imread(frame_url)
            return frame
    except Exception as e:
        print(f"❌ Error downloading frame: {e}")
        return None
