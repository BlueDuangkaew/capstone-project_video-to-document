# tests/test_frame_detection.py

from src.frame_detection.detector import SceneDetector
from src.frame_detection.keyframe_selector import KeyframeExtractor
import cv2
import numpy as np

def test_scene_detector_runs():
    detector = SceneDetector()
    scenes = detector.detect_scenes("tests/sample.mp4")
    assert isinstance(scenes, list)

def test_variance_of_laplacian():
    img = np.zeros((100,100), dtype=np.uint8)
    sharpness = cv2.Laplacian(img, cv2.CV_64F).var()
    assert sharpness == 0.0  # perfectly flat image

def test_keyframe_extractor_mock():
    extractor = KeyframeExtractor()
    # We only test that function exists; real video tested in integration test
    assert extractor.blur_threshold > 0
