import os
import io
import requests
from flask import Flask, request, jsonify
from PIL import Image
import torch

# YOLOX imports
from yolox.exp import get_exp
from yolox.utils import postprocess
from yolox.data.data_augment import preproc

app = Flask(__name__)

YOLOX_MODEL = "yolox_nano"
YOLOX_WEIGHTS = "yolox_nano.pth"

# Load YOLOX-nano experiment and model
exp = get_exp(f"exps/default/{YOLOX_MODEL}.py", None)
model = exp.get_model()
ckpt = torch.load(YOLOX_WEIGHTS, map_location="cpu")
model.load_state_dict(ckpt["model"])
model.eval()

COCO_CLASSES = (
    "person", "bicycle", "car", "motorcycle", "airplane", "bus",
    "train", "truck", "boat", "traffic light", "fire hydrant", "stop sign",
    "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag",
    "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite",
    "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana",
    "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza",
    "donut", "cake", "chair", "couch", "potted plant", "bed", "dining table",
    "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
    "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock",
    "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
)

def get_image_from_url(url):
    response = requests.get(url)
    img = Image.open(io.BytesIO(response.content)).convert("RGB")
    return img

def detect_football_objects(image):
    image = np.array(image)
    img, ratio = preproc(image, exp.test_size, swap=(2, 0, 1))
    img = torch.from_numpy(img).unsqueeze(0)
    with torch.no_grad():
        outputs = model(img)
        outputs = postprocess(outputs, exp.num_classes, exp.test_conf, exp.nmsthre)
    detections = []
    if outputs[0] is not None:
        for det in outputs[0].cpu():
            x0, y0, x1, y1, score, cls_id = det
            cls_id = int(cls_id)
            label = COCO_CLASSES[cls_id]
            if label not in ["person", "sports ball"]:
                continue
            bbox = [int(x0), int(y0), int(x1), int(y1)]
            detections.append({
                "label": label,
                "bbox": bbox,
                "score": float(score)
            })
    return detections

@app.route("/detect", methods=["POST"])
def detect():
    data = request.get_json()
    image_url = data.get("image_url")
    if not image_url:
        return jsonify({"success": False, "error": "Missing image_url"}), 400
    try:
        image = get_image_from_url(image_url)
        detections = detect_football_objects(image)
        return jsonify({"success": True, "detections": detections, "frame_url": image_url})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "model": YOLOX_MODEL})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
