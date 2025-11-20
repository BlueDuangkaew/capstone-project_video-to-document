import os
from src.frame_detection.detector import SceneDetector
from src.frame_detection.keyframe_selector import KeyframeExtractor
from src.frame_detection.utils import ensure_dir, frame_save_path

def extract_frames(video_path: str, output_dir: str):
    ensure_dir(output_dir)

    detector = SceneDetector(threshold=0.35)
    extractor = KeyframeExtractor()

    scenes = detector.detect_scenes(video_path)

    saved_frames = []

    for idx, scene in enumerate(scenes):
        path = frame_save_path(output_dir, idx)
        saved = extractor.extract_keyframe(video_path, scene, save_path=path)
        if saved:
            saved_frames.append(saved)

    return saved_frames
