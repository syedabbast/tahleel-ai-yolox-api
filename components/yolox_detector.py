"""
YOLOX Detector Module - TAHLEEL.ai Football Tactical Analysis

Purpose:
- Run YOLOX-S detection on extracted match frames (players, ball)
- Separate teams by jersey color using k-means clustering
- Track players across frames (motpy/SORT)
- Output detections (coordinates, jersey color/team, consistent IDs) for tactical processor

Business context:
- NO MOCK DATA: Only real detections from YOLOX-S
- 5-minute analysis performance required for Arab League clubs

Dependencies:
- torch
- yolox
- opencv-python
- numpy
- scikit-learn (k-means)
- motpy (player tracking)
"""

import torch
import cv2
import numpy as np
from sklearn.cluster import KMeans
from motpy import MultiObjectTracker
from yolox.exp import get_exp
from yolox.utils import postprocess
from yolox.data.data_augment import preproc

# --- CONFIG ---
YOLOX_MODEL_PATH = 'models/yolox_s.pth'
NUM_TEAMS = 2
JERSEY_SAMPLE_PIXELS = 100
CONFIDENCE_THRESHOLD = 0.4
NMS_THRESHOLD = 0.45

def load_yolox_model(device='cpu'):
    """
    Load YOLOX-S model from weights file.
    """
    exp = get_exp('yolox_s', None)
    model = exp.get_model()
    model.eval()
    ckpt = torch.load(YOLOX_MODEL_PATH, map_location=device)
    model.load_state_dict(ckpt['model'])
    model.to(device)
    return model, exp

def get_jersey_color_crop(frame, bbox, sample_pixels=JERSEY_SAMPLE_PIXELS):
    """
    Extract jersey color from player bounding box (center upper region).
    Returns mean RGB value.
    """
    x1, y1, x2, y2 = [int(coord) for coord in bbox]
    crop = frame[y1:y2, x1:x2]
    if crop.size == 0:
        return [0, 0, 0]
    h, w, _ = crop.shape
    # Focus on upper-middle region for jersey (avoid shorts/socks/grass)
    crop_region = crop[max(0, int(h*0.2)):int(h*0.6), int(w*0.3):int(w*0.7)]
    pixels = crop_region.reshape(-1, 3)
    # Sample random pixels if too many
    if len(pixels) > sample_pixels:
        idx = np.random.choice(len(pixels), sample_pixels, replace=False)
        pixels = pixels[idx]
    mean_rgb = np.mean(pixels, axis=0).astype(int)
    return mean_rgb.tolist()

def separate_teams_by_color(jersey_rgbs, num_teams=NUM_TEAMS):
    """
    Cluster jersey RGBs using k-means to assign team labels.
    Returns team labels (0, 1) for each player.
    """
    kmeans = KMeans(n_clusters=num_teams, random_state=42, n_init=10)
    labels = kmeans.fit_predict(jersey_rgbs)
    team_centers = kmeans.cluster_centers_
    return labels, team_centers

def run_yolox_detection(frame_urls, device='cpu'):
    """
    Run YOLOX-S detection on list of frame URLs.
    Returns list of detections: [{
        frame_number, player_detections: [{bbox, conf, jersey_rgb, team_label, track_id}], ball_detections: [...]
    }, ...]
    """
    # Load YOLOX model once
    model, exp = load_yolox_model(device)
    input_size = exp.test_size

    # Initialize multi-object tracker for player tracking
    tracker = MultiObjectTracker(dt=1/5, tracker_kwargs={'max_staleness': 5})

    all_detections = []
    jersey_rgbs_batch = []

    for frame_idx, frame_url in enumerate(frame_urls):
        # --- Load frame from GCS/local ---
        frame = load_frame_from_gcs(frame_url)  # Implement this in utils.cloud_storage for GCS
        if frame is None:
            continue

        # --- Preprocess frame for YOLOX ---
        img, ratio = preproc(frame, input_size, swap=(2, 0, 1))
        img_tensor = torch.from_numpy(img).unsqueeze(0).float()
        img_tensor = img_tensor.to(device)

        # --- Inference ---
        with torch.no_grad():
            outputs = model(img_tensor)
            outputs = postprocess(outputs, num_classes=exp.num_classes, conf_thre=CONFIDENCE_THRESHOLD, nms_thre=NMS_THRESHOLD)
        
        if outputs[0] is None:
            all_detections.append({
                'frame_number': frame_idx,
                'player_detections': [],
                'ball_detections': []
            })
            continue

        detections_frame = outputs[0].cpu().numpy()
        player_bboxes = []
        ball_bboxes = []
        jersey_rgbs = []
        detection_objs = []

        # --- Parse detections ---
        for det in detections_frame:
            x1, y1, x2, y2, conf, cls = det
            bbox = [x1/ratio, y1/ratio, x2/ratio, y2/ratio]  # Rescale to original image
            cls_id = int(cls)
            if cls_id == 0:  # person/player
                jersey_rgb = get_jersey_color_crop(frame, bbox)
                jersey_rgbs.append(jersey_rgb)
                player_bboxes.append({
                    'bbox': bbox,
                    'conf': float(conf),
                    'jersey_rgb': jersey_rgb,
                })
            elif cls_id == 32:  # sports ball (COCO class)
                ball_bboxes.append({
                    'bbox': bbox,
                    'conf': float(conf)
                })

        # --- Team separation (after batch) ---
        jersey_rgbs_batch.extend(jersey_rgbs)

        # --- Player tracking ---
        tracks = tracker.step(
            [{'bbox': p['bbox'], 'score': p['conf'], 'class_id': 0} for p in player_bboxes],
            frame_id=frame_idx
        )
        for i, p in enumerate(player_bboxes):
            p['track_id'] = tracks[i].id if i < len(tracks) else None

        detection_objs = player_bboxes

        all_detections.append({
            'frame_number': frame_idx,
            'player_detections': detection_objs,
            'ball_detections': ball_bboxes
        })

    # --- Team separation: Run k-means across all jersey RGBs ---
    if jersey_rgbs_batch:
        team_labels, team_rgbs = separate_teams_by_color(jersey_rgbs_batch, num_teams=NUM_TEAMS)
        # Assign team labels back to player detections
        det_idx = 0
        for det_frame in all_detections:
            for player in det_frame['player_detections']:
                if det_idx < len(team_labels):
                    player['team_label'] = int(team_labels[det_idx])
                    player['team_rgb'] = [int(x) for x in team_rgbs[player['team_label']]]
                    det_idx += 1

    return all_detections

def load_frame_from_gcs(frame_url):
    """
    Load frame image from GCS URL.
    Returns numpy array (OpenCV BGR).
    """
    # Use google-cloud-storage to download, then cv2.imread
    # If local, use cv2.imread directly
    import tempfile
    from google.cloud import storage

    try:
        if frame_url.startswith('gs://'):
            client = storage.Client()
            bucket_name, blob_path = frame_url.replace('gs://', '').split('/', 1)
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            with tempfile.NamedTemporaryFile(delete=True, suffix='.jpg') as tmp:
                blob.download_to_filename(tmp.name)
                frame = cv2.imread(tmp.name)
                return frame
        else:
            # Local path
            frame = cv2.imread(frame_url)
            return frame
    except Exception as e:
        print(f"❌ Error loading frame from {frame_url}: {e}")
        return None
