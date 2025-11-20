import cv2
import numpy as np
from typing import List, Dict, Optional

def variance_of_laplacian(image):
    """High value = sharper image."""
    return cv2.Laplacian(image, cv2.CV_64F).var()

class KeyframeExtractor:
    def __init__(self, blur_threshold: float = 120.0):
        self.blur_threshold = blur_threshold

    def extract_keyframe(
        self,
        video_path: str,
        scene: Dict,
        save_path: Optional[str] = None
    ) -> Optional[str]:

        cap = cv2.VideoCapture(video_path)
        start = scene["start_frame"]
        end = scene["end_frame"]
        mid = (start + end) // 2

        cap.set(cv2.CAP_PROP_POS_FRAMES, mid)
        ret, frame = cap.read()
        if not ret:
            return None

        # Skip blurry frames
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if variance_of_laplacian(gray) < self.blur_threshold:
            return None

        if save_path:
            cv2.imwrite(save_path, frame)

        cap.release()
        return save_path
