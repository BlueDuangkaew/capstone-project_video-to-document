import pytest

from src.frame_detection.detector import SceneDetector


def test_detect_scenes_none_raises():
    det = SceneDetector()
    with pytest.raises(FileNotFoundError):
        det.detect_scenes(None)


def test_detect_scenes_missing_file_raises():
    det = SceneDetector()
    scenes = det.detect_scenes("/non/existent/path.mp4")
    assert isinstance(scenes, list)
    assert len(scenes) == 0
