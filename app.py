"""
TAHLEEL.ai - YOLOx Detection + Claude AI Tactical Analysis
"""

import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from gcs_helper import upload_file, download_file
import torch
import cv2
import numpy as np
import tempfile
from google.cloud import storage
from anthropic import Anthropic

sys.path.insert(0, '/yolox')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

YOLOX_WEIGHTS = "gs://tahleel-ai-videos/models/yolox_m.pth"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
claude_client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

def download_model_from_gcs(gcs_path, local_path):
    if os.path.exists(local_path):
        return local_path
    if gcs_path.startswith("gs://"):
        gcs_path = gcs_path[5:]
    parts = gcs_path.split("/", 1)
    client = storage.Client()
    bucket = client.bucket(parts[0])
    blob = bucket.blob(parts[1])
    blob.download_to_filename(local_path)
    return local_path

def load_yolox():
    from yolox.exp import get_exp
    from yolox.utils import postprocess
    
    local_weights = "/tmp/yolox_m.pth"
    download_model_from_gcs(YOLOX_WEIGHTS, local_weights)
    
    exp = get_exp(None, "yolox-m")
    model = exp.get_model()
    ckpt = torch.load(local_weights, map_location="cpu")
    model.load_state_dict(ckpt["model"])
    model.eval()
    
    return model, exp, postprocess

def preprocess(img, input_size=(640, 640)):
    img = cv2.resize(img, input_size)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32)
    return torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0)

def analyze_with_claude(summary):
    if not claude_client:
        return {"error": "Claude not configured"}
    try:
        message = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": f"""Analyze this football match data:

{summary}

Provide tactical insights:
1. Formation Analysis
2. Player Movement Patterns  
3. Attacking vs Defensive Balance
4. Key Observations
5. Coach Recommendations"""}]
        )
        return {"analysis": message.content[0].text}
    except Exception as e:
        return {"error": str(e)}

print("🚀 Loading YOLOx...")
yolox_model, yolox_exp, yolox_postprocess = load_yolox()
print("✅ YOLOx ready")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "yolox_loaded": True,
        "claude_configured": claude_client is not None
    })

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files['file']
    temp_path = os.path.join(tempfile.gettempdir(), file.filename)
    file.save(temp_path)
    gcs_path = f"videos/{file.filename}"
    url = upload_file(temp_path, gcs_path)
    os.remove(temp_path)
    return jsonify({"success": True, "gcs_url": url, "gcs_path": gcs_path})

@app.route("/analyze", methods=["POST"])
def analyze():
    gcs_path = request.json.get("gcs_path")
    temp_path = os.path.join(tempfile.gettempdir(), os.path.basename(gcs_path))
    download_file(gcs_path, temp_path)

    cap = cv2.VideoCapture(temp_path)
    results = []
    total_detections = 0
    frame_num = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_num % 30 == 0:
            img_tensor = preprocess(frame)
            with torch.no_grad():
                outputs = yolox_model(img_tensor)
            
            # Use YOLOx native postprocessing
            outputs = yolox_postprocess(
                outputs, 
                num_classes=80,
                conf_thre=0.25,
                nms_thre=0.45
            )
            
            if outputs[0] is not None:
                dets = outputs[0].cpu().numpy()
                num_dets = len(dets)
            else:
                num_dets = 0
            
            total_detections += num_dets
            results.append({"frame": frame_num, "detections": num_dets})
            print(f"✅ Frame {frame_num}: {num_dets} detections")
        frame_num += 1
    
    cap.release()
    os.remove(temp_path)

    summary = f"Video: {gcs_path}\nFrames: {frame_num}\nTotal Detections: {total_detections}\n{results[:5]}"
    claude_analysis = analyze_with_claude(summary)

    return jsonify({
        "success": True,
        "detections": {
            "total": total_detections,
            "frames_analyzed": len(results),
            "frame_results": results
        },
        "tactical_analysis": claude_analysis,
        "message": "YOLOx + Claude analysis complete"
    })

@app.route("/frames/<prefix>", methods=["GET"])
def frames(prefix):
    from gcs_helper import list_files
    return jsonify({"frames": list_files(f"frames/{prefix}")})
