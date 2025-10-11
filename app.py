"""
TAHLEEL.ai GCP Cloud Run Backend
Production Flask API for tactical video analysis and GCS integration

Author: Syed (Auwire Technologies)
"""

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from gcs_helper import upload_file, download_file, list_files
import torch
import cv2
from PIL import Image
import tempfile

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Load YOLOX model (nano for speed)
YOLOX_WEIGHTS = os.environ.get("YOLOX_WEIGHTS", "yolox_nano.pth")
YOLOX_MODEL_NAME = os.environ.get("YOLOX_MODEL_NAME", "yolox-nano")

def load_yolox_model():
    # Placeholder: replace with actual YOLOX load for real implementation
    # Example:
    # model = torch.hub.load('Megvii-BaseDetection/YOLOX', YOLOX_MODEL_NAME, pretrained=False)
    # model.load_state_dict(torch.load(YOLOX_WEIGHTS, map_location='cpu'))
    # model.eval()
    # return model
    return None

yolox_model = load_yolox_model()

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "TAHLEEL.ai GCP backend",
        "yolox_loaded": yolox_model is not None,
        "bucket": os.environ.get("GCS_BUCKET_NAME", "tahleel-ai-videos"),
        "timestamp": str(os.environ.get("CURRENT_TIMESTAMP", "")),
    })

@app.route("/upload", methods=["POST"])
def upload_video():
    if 'file' not in request.files:
        return jsonify({"error": "No file in request"}), 400
    file = request.files['file']
    filename = file.filename
    temp_path = os.path.join(tempfile.gettempdir(), filename)
    file.save(temp_path)
    gcs_path = f"videos/{filename}"
    public_url = upload_file(temp_path, gcs_path)
    os.remove(temp_path)
    return jsonify({"success": True, "gcs_url": public_url, "gcs_path": gcs_path})

@app.route("/analyze", methods=["POST"])
def analyze_video():
    data = request.get_json()
    gcs_path = data.get("gcs_path")
    if not gcs_path:
        return jsonify({"error": "Missing gcs_path"}), 400

    temp_path = os.path.join(tempfile.gettempdir(), os.path.basename(gcs_path))
    try:
        download_file(gcs_path, temp_path)
    except Exception as e:
        return jsonify({"error": f"Failed to download from GCS: {str(e)}"}), 500

    cap = cv2.VideoCapture(temp_path)
    frame_results = []
    frame_count = 0
    sampling_rate = 30

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % sampling_rate == 0:
            # Placeholder: run YOLOX detection
            # result = yolox_model(frame) if yolox_model else {}
            result = {"frame": frame_count, "detections": []}
            frame_results.append(result)
        frame_count += 1
    cap.release()
    os.remove(temp_path)

    return jsonify({
        "success": True,
        "frames_analyzed": len(frame_results),
        "frame_results": frame_results,
        "gcs_path": gcs_path,
        "message": "Analysis complete (REAL video, mock detection - replace with YOLOX, GPT Vision, Claude)"
    })

@app.route("/frames/<prefix>", methods=["GET"])
def list_frames(prefix):
    files = list_files(f"frames/{prefix}")
    return jsonify({"frames": files})

# Gunicorn will run: app:app
# No need for __main__ block in Cloud Run
