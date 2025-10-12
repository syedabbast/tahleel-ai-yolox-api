"""
Supabase Utility - TAHLEEL.ai Tactical Analysis

Purpose:
- Upload tactical analysis JSON results to Supabase database
- Enables dual save: results stored in BOTH GCS and Supabase
- Used for dashboard/history, Claude AI reading, frontend display

Business context:
- NO MOCK DATA: Only real results stored for paying teams
- Supports enterprise-grade reliability and multi-user access

Dependencies:
- supabase-py (Python client for Supabase)
- os (for env vars)
"""

import os
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise Exception("Supabase credentials missing in environment variables")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def upload_json_to_supabase(json_data, video_id):
    """
    Upload tactical JSON result to Supabase 'analyses' table.
    Returns row ID or error.
    """
    try:
        client = get_supabase_client()
        # Insert result into 'analyses' table
        response = client.table("analyses").insert({
            "video_id": video_id,
            "analysis_data": json_data,
            "status": json_data.get("status", "success"),
            "created_at": json_data.get("video_metadata", {}).get("created_at"),
            "confidence_score": json_data.get("teams", {}).get("team_b", {}).get("formation_confidence", 0.0)
        }).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]["id"]
        else:
            print("❌ Error uploading result to Supabase:", response.error)
            return None
    except Exception as e:
        print(f"❌ Supabase upload error: {e}")
        return None
