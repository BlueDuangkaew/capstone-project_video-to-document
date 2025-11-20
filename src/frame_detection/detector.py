import cv2
import numpy as np
from typing import List, Dict

class SceneDetector:
    def __init__(self, threshold: float = 0.35):
        """
        threshold: sensitivity for detecting scene change.
        Higher = fewer scenes.
        """
        self.threshold = threshold

    def detect_scenes(self, video_path: str) -> List[Dict]:
        cap = cv2.VideoCapture(video_path)
        prev_hist = None
        scenes = []
        scene_start = 0
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist = cv2.normalize(hist, hist).flatten()

            if prev_hist is not None:
                diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA)

                # new scene
                if diff > self.threshold:
                    scenes.append({"start_frame": scene_start, "end_frame": frame_idx})
                    scene_start = frame_idx + 1

            prev_hist = hist
            frame_idx += 1

        # final scene
        scenes.append({"start_frame": scene_start, "end_frame": frame_idx})
        cap.release()
        return scenes
