"""
Video file validation
"""

from fastapi import UploadFile, HTTPException

MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB
ALLOWED_FORMATS = ["video/mp4", "video/mpeg", "video/quicktime"]

def validate_video_file(video: UploadFile):
    """Validate uploaded video file"""
    
    # Check content type
    if video.content_type not in ALLOWED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format. Allowed: {ALLOWED_FORMATS}"
        )
    
    # Check file size (approximate)
    video.file.seek(0, 2)
    size = video.file.tell()
    video.file.seek(0)
    
    if size > MAX_VIDEO_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max: {MAX_VIDEO_SIZE // 1024 // 1024}MB"
        )
    
    return True
