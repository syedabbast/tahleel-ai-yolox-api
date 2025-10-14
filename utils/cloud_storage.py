"""
Google Cloud Storage helper functions
"""

import os
import json
from google.cloud import storage

GCS_BUCKET = os.getenv("GCS_BUCKET_NAME", "tahleel-ai-videos")

def upload_video_to_gcs(video_file, video_id):
    """Upload video to GCS, return gs:// URL"""
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET)
        blob_path = f"videos/{video_id}.mp4"
        blob = bucket.blob(blob_path)
        
        blob.upload_from_file(video_file.file, content_type="video/mp4")
        return f"gs://{GCS_BUCKET}/{blob_path}"
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return None

def upload_json_to_gcs(data, video_id):
    """Upload JSON results to GCS"""
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET)
        blob_path = f"results/{video_id}.json"
        blob = bucket.blob(blob_path)
        
        blob.upload_from_string(
            json.dumps(data, indent=2),
            content_type="application/json"
        )
        return f"gs://{GCS_BUCKET}/{blob_path}"
    except Exception as e:
        print(f"❌ JSON upload failed: {e}")
        return None

def get_analysis_result_from_gcs(video_id):
    """Retrieve analysis JSON from GCS"""
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(f"results/{video_id}.json")
        
        if not blob.exists():
            return None
            
        return json.loads(blob.download_as_string())
    except Exception as e:
        print(f"❌ Retrieval failed: {e}")
        return None
