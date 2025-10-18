"""
TAHLEEL.ai GCP Cloud Run Backend
Production Flask API for tactical video analysis and GCS integration

Author: Syed (Auwire Technologies)
"""

import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from gcs_helper import upload_file, download_file, list_files
import torch
import cv2
import numpy as np
from PIL import Image
import tempfile
from google.cloud import storage

# Add YOLOx to path
sys.path.insert(0, '/yolox')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# YOLOx configuration
YOLOX_WEIGHTS = os.environ.get("YOLOX_WEIGHTS", "gs://tahleel-ai-videos/models/yolox_m.pth")
YOLOX_MODEL_NAME = os.environ.get("YOLOX_MODEL_NAME", "yolox-m")
YOLOX_INPUT_SIZE = (640, 640)
CONFIDENCE_THRESHOLD = 0.3  # Lower threshold

def download_model_from_gcs(gcs_path, local_path):
    """Download YOLOx weights from GCS"""
    if os.path.exists(local_path):
        print(f"✅ Model already exists at {local_path}")
        return local_path
    
    print(f"📥 Downloading model from {gcs_path}")
    
    if gcs_path.startswith("gs://"):
        gcs_path = gcs_path[5:]
    
    parts = gcs_path.split("/", 1)
    bucket_name = parts[0]
    blob_name = parts[1] if len(parts) > 1 else ""
    
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_path)
    
    print(f"✅ Model downloaded to {local_path}")
    return local_path

def load_yolox_model():
    """Load REAL YOLOx model"""
    try:
        print("🔄 Loading YOLOx model...")
        
        from yolox.exp import get_exp
        
        local_weights = "/tmp/yolox_m.pth"
        download_model_from_gcs(YOLOX_WEIGHTS, local_weights)
        
        exp = get_exp(None, YOLOX_MODEL_NAME)
        model = exp.get_model()
        
        ckpt = torch.load(local_weights, map_location="cpu")
        model.load_state_dict(ckpt["model"])
        model.eval()
        
        print("✅ YOLOx model loaded successfully!")
        return model, exp
        
    except Exception as e:
        print(f"❌ Error loading YOLOx: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

def preprocess_frame(frame, input_size=(640, 640)):
    """Preprocess frame for YOLOx inference"""
    img = cv2.resize(frame, input_size)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img_tensor = torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0)
    return img_tensor

def postprocess_yolox(outputs, conf_threshold=0.3):
    """Process YOLOx raw outputs"""
    if outputs is None:
        return []
    
    # YOLOx returns tuple of tensors
    # outputs shape: [batch, num_predictions, 85] where 85 = 4(bbox) + 1(obj) + 80(classes)
    if isinstance(outputs, tuple):
        outputs = outputs[0]
    
    detections = []
    output = outputs[0].cpu().numpy()  # Get first batch
    
    # Filter by objectness score
    obj_conf = output[:, 4]
    mask = obj_conf > conf_threshold
    filtered = output[mask]
    
    print(f"   Raw detections: {len(output)}, After filtering (conf>{conf_threshold}): {len(filtered)}")
    
    for det in filtered:
        x, y, w, h = det[:4]
        obj_conf = det[4]
        class_scores = det[5:]
        class_id = np.argmax(class_scores)
        class_conf = class_scores[class_id]
        
        detections.append({
            "bbox": [float(x), float(y), float(w), float(h)],
            "confidence": float(obj_conf * class_conf),
            "class_id": int(class_id),
            "obj_conf": float(obj_conf)
        })
    
    return detections

# Load model on startup
print("🚀 Initializing YOLOx model...")
yolox_model, yolox_exp = load_yolox_model()

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "TAHLEEL.ai GCP backend",
        "yolox_loaded": yolox_model is not None,
        "bucket": os.environ.get("GCS_BUCKET_NAME", "tahleel-ai-videos"),
        "timestamp": "",
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
    if yolox_model is None:
        return jsonify({"error": "YOLOx model not loaded"}), 500
        
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

    print(f"📹 Processing video: {gcs_path}")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % sampling_rate == 0:
            try:
                img_tensor = preprocess_frame(frame, YOLOX_INPUT_SIZE)
                
                with torch.no_grad():
                    outputs = yolox_model(img_tensor)
                
                filtered_detections = postprocess_yolox(outputs, CONFIDENCE_THRESHOLD)
                
                result = {
                    "frame": frame_count,
                    "detections": filtered_detections[:50],  # Limit to 50 per frame
                    "num_detections": len(filtered_detections)
                }
                frame_results.append(result)
                print(f"✅ Frame {frame_count}: {len(filtered_detections)} detections")
                
            except Exception as e:
                print(f"❌ Error processing frame {frame_count}: {str(e)}")
                import traceback
                traceback.print_exc()
                result = {
                    "frame": frame_count,
                    "detections": [],
                    "error": str(e)
                }
                frame_results.append(result)
                
        frame_count += 1
    
    cap.release()
    os.remove(temp_path)

    print(f"✅ Analysis complete: {len(frame_results)} frames processed")

    return jsonify({
        "success": True,
        "frames_analyzed": len(frame_results),
        "total_frames": frame_count,
        "frame_results": frame_results,
        "gcs_path": gcs_path,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "message": "REAL YOLOx detection complete"
    })

@app.route("/frames/<prefix>", methods=["GET"])
def list_frames(prefix):
    files = list_files(f"frames/{prefix}")
    return jsonify({"frames": files})
