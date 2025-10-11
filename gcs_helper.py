"""
Google Cloud Storage Helper for TAHLEEL.ai
Production-ready GCS integration for video/frame/results upload/download.
"""

import os
from google.cloud import storage

GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "tahleel-ai-videos")

def get_gcs_client():
    return storage.Client()

def upload_file(local_path, gcs_path, bucket_name=None):
    bucket_name = bucket_name or GCS_BUCKET_NAME
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    blob.upload_from_filename(local_path)
    blob.make_public()
    return blob.public_url

def upload_bytes(data, gcs_path, bucket_name=None):
    bucket_name = bucket_name or GCS_BUCKET_NAME
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    blob.upload_from_string(data)
    blob.make_public()
    return blob.public_url

def download_file(gcs_path, local_path, bucket_name=None):
    bucket_name = bucket_name or GCS_BUCKET_NAME
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    blob.download_to_filename(local_path)
    return local_path

def list_files(prefix="", bucket_name=None):
    bucket_name = bucket_name or GCS_BUCKET_NAME
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    return [b.name for b in bucket.list_blobs(prefix=prefix)]

def get_signed_url(gcs_path, expires=3600, bucket_name=None):
    bucket_name = bucket_name or GCS_BUCKET_NAME
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    return blob.generate_signed_url(expiration=expires)
