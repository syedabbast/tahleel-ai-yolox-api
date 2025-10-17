"""TAHLEEL.ai - REAL YOLOx Detection - NO MOCK DATA"""
import torch
import cv2
import numpy as np
from sklearn.cluster import KMeans
from google.cloud import storage
import logging
import os
import tempfile
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GCS_BUCKET = os.getenv("GCS_BUCKET_NAME", "tahleel-ai-videos")

class YOLOXDetector:
    def __init__(self, model_name="yolox_m", device="cpu"):
        self.device = device
        self.model_name = model_name
        self.model = None
        self.conf_thresh = 0.25
        self.nms_thresh = 0.45
        logger.info(f"🔧 YOLOXDetector: {model_name} on {device}")
        self._load_model()
    
    def _load_model(self):
        try:
            logger.info("📦 Loading YOLOx from GCS...")
            weights_path = self._download_weights_from_gcs()
            if not weights_path:
                raise FileNotFoundError("Weights not found")
            
            from yolox.exp import get_exp
            exp = get_exp(None, "yolox-m")
            self.model = exp.get_model()
            
            ckpt = torch.load(weights_path, map_location=self.device)
            self.model.load_state_dict(ckpt["model"])
            self.model.to(self.device)
            self.model.eval()
            
            self.num_classes = exp.num_classes
            self.test_size = exp.test_size
            logger.info("✅ YOLOx loaded!")
        except Exception as e:
            logger.error(f"❌ Load failed: {e}")
            raise
    
    def _download_weights_from_gcs(self):
        try:
            client = storage.Client()
            bucket = client.bucket(GCS_BUCKET)
            blob = bucket.blob(f"models/{self.model_name}.pth")
            
            local_dir = Path("/tmp/yolox_models")
            local_dir.mkdir(exist_ok=True)
            local_path = local_dir / f"{self.model_name}.pth"
            
            if not local_path.exists():
                logger.info(f"📥 Downloading {self.model_name}.pth...")
                blob.download_to_filename(str(local_path))
                logger.info("✅ Downloaded")
            else:
                logger.info("✅ Using cached weights")
            
            return str(local_path)
        except Exception as e:
            logger.error(f"❌ Download failed: {e}")
            return None
    
    def _download_frame_from_gcs(self, frame_url):
        try:
            parts = frame_url.replace("gs://", "").split("/", 1)
            bucket_name = parts[0]
            blob_path = parts[1]
            
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            blob.download_to_filename(temp_file.name)
            
            frame = cv2.imread(temp_file.name)
            os.unlink(temp_file.name)
            return frame
        except Exception as e:
            logger.error(f"❌ Frame download failed: {e}")
            return None
    
    def _preprocess_frame(self, frame):
        img = cv2.resize(frame, self.test_size)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1))
        img = np.expand_dims(img, axis=0)
        return torch.from_numpy(img).to(self.device)
    
    def _detect_on_frame(self, frame):
        try:
            if frame is None:
                return []
            
            img_tensor = self._preprocess_frame(frame)
            h, w = frame.shape[:2]
            
            with torch.no_grad():
                outputs = self.model(img_tensor)
            
            from yolox.utils import postprocess
            outputs = postprocess(outputs, self.num_classes, self.conf_thresh, self.nms_thresh, class_agnostic=True)
            
            if outputs[0] is None:
                return []
            
            outputs = outputs[0].cpu().numpy()
            ratio = min(self.test_size[0] / h, self.test_size[1] / w)
            
            detections = []
            for det in outputs:
                x1, y1, x2, y2, obj_conf, cls_conf, cls_id = det
                
                if int(cls_id) != 0:
                    continue
                
                x1, y1, x2, y2 = int(x1/ratio), int(y1/ratio), int(x2/ratio), int(y2/ratio)
                conf = obj_conf * cls_conf
                
                if conf < self.conf_thresh:
                    continue
                
                detections.append({
                    'bbox': [x1, y1, x2, y2],
                    'conf': float(conf),
                    'class_id': int(cls_id),
                    'class_name': 'person'
                })
            
            return detections
        except Exception as e:
            logger.error(f"❌ Detection failed: {e}")
            return []
    
    def _assign_teams(self, frame, detections):
        try:
            if len(detections) < 2:
                for det in detections:
                    det['team_id'] = 0
                return detections
            
            colors = []
            valid_dets = []
            
            for det in detections:
                x1, y1, x2, y2 = det['bbox']
                crop = frame[max(0,y1):min(frame.shape[0],y2), max(0,x1):min(frame.shape[1],x2)]
                
                if crop.size == 0:
                    continue
                
                upper = crop[:crop.shape[0]//3, :]
                if upper.size == 0:
                    continue
                
                colors.append(upper.mean(axis=(0,1)))
                valid_dets.append(det)
            
            if len(colors) < 2:
                for det in detections:
                    det['team_id'] = 0
                return detections
            
            kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
            labels = kmeans.fit_predict(np.array(colors))
            
            for det, label in zip(valid_dets, labels):
                det['team_id'] = int(label)
            
            return valid_dets
        except Exception as e:
            logger.error(f"❌ Team assignment failed: {e}")
            for det in detections:
                det['team_id'] = 0
            return detections

def run_yolox_detection(frame_urls, device='cpu'):
    logger.info(f"🔍 REAL YOLOx detection on {len(frame_urls)} frames")
    detector = YOLOXDetector("yolox_m", device)
    all_detections = []
    
    for idx, frame_url in enumerate(frame_urls):
        try:
            frame = detector._download_frame_from_gcs(frame_url)
            if frame is None:
                all_detections.append({'frame_number': idx, 'frame_url': frame_url, 'player_detections': [], 'ball_detections': [], 'error': 'Download failed'})
                continue
            
            detections = detector._detect_on_frame(frame)
            detections = detector._assign_teams(frame, detections)
            players = [d for d in detections if d['class_name'] == 'person']
            
            all_detections.append({
                'frame_number': idx,
                'frame_url': frame_url,
                'player_detections': players,
                'ball_detections': [],
                'total_players': len(players)
            })
            
            if (idx + 1) % 10 == 0:
                logger.info(f"✅ Processed {idx + 1}/{len(frame_urls)}")
        except Exception as e:
            logger.error(f"❌ Frame {idx} error: {e}")
            all_detections.append({'frame_number': idx, 'frame_url': frame_url, 'player_detections': [], 'ball_detections': [], 'error': str(e)})
    
    total = sum(d.get('total_players', 0) for d in all_detections)
    avg = total / len(all_detections) if all_detections else 0
    logger.info(f"🎉 Complete! Avg players: {avg:.1f}")
    return all_detections

def load_yolox_model(device='cpu'):
    try:
        detector = YOLOXDetector("yolox_m", device)
        return detector.model
    except:
        return None
