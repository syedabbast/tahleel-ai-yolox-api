"""
Video Validation Utility - TAHLEEL.ai Tactical Analysis

Purpose:
- Validate uploaded football video files for format, size, and duration
- Enforce business rules: only REAL videos, no mock/test data
- Prevent backend overload and ensure high-value customer compliance

Business context:
- Arab League clients ($15K-$45K/month) expect real analysis
- Invalid files = analysis errors and business risk

Dependencies:
- OpenCV (cv2)
"""

import cv2

ALLOWED_EXTENSIONS = ['.mp4', '.mov', '.avi', '.webm']
MAX_FILE_SIZE_MB = 500
MAX_VIDEO_DURATION_SEC = 900  # 15 minutes

def validate_video_file(video_file):
    """
    Validate video file for type, size, and duration.
    Raises Exception with clear error if invalid.
    """
    filename = video_file.filename
    ext = filename.lower().split('.')[-1]
    if f'.{ext}' not in ALLOWED_EXTENSIONS:
        raise Exception(f"Invalid video format: {filename}. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Check file size
    video_file.file.seek(0, 2)  # Seek to end
    size_mb = video_file.file.tell() / (1024 * 1024)
    video_file.file.seek(0)
    if size_mb > MAX_FILE_SIZE_MB:
        raise Exception(f"File size {size_mb:.2f}MB exceeds limit of {MAX_FILE_SIZE_MB}MB")

    # Save to temp for duration check
    import tempfile
    with tempfile.NamedTemporaryFile(delete=True, suffix=f'.{ext}') as tmp:
        tmp.write(video_file.file.read())
        tmp.flush()
        cap = cv2.VideoCapture(tmp.name)
        if not cap.isOpened():
            raise Exception("Failed to open video file for validation")
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_sec = frame_count / fps
        cap.release()
        video_file.file.seek(0)  # Reset for next use

        if duration_sec > MAX_VIDEO_DURATION_SEC:
            raise Exception(f"Video duration {duration_sec:.2f}s exceeds max allowed of {MAX_VIDEO_DURATION_SEC}s (15 minutes)")

    return True
