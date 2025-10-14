import os
import json
from google.cloud import storage

GCS_BUCKET = os.getenv("GCS_BUCKET_NAME", "tahleel-ai-videos")

async def upload_video_to_gcs(video_file, video_id):
    try:
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(f"videos/{video_id}.mp4")
        
        content = await video_file.read()
        blob.upload_from_string(content, content_type="video/mp4")
        
        return f"gs://{GCS_BUCKET}/videos/{video_id}.mp4"
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return None
