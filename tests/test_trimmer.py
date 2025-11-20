from src.trimmer.video_trimmer import VideoTrimmer
import os

def test_trimming():
    trimmer = VideoTrimmer("test_segments")
    output = trimmer.trim("tests/sample_video.mp4", 0, 2)
    assert os.path.exists(output)

def test_auto_segment():
    trimmer = VideoTrimmer("test_segments")
    segments = trimmer.auto_segment("tests/sample_video.mp4")
    assert len(segments) > 0
