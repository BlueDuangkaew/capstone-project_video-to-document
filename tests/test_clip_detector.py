import tempfile
import os
import pytest

from pathlib import Path


def ffmpeg_available():
    from shutil import which
    return which("ffmpeg") is not None


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg not available")
def test_detect_action_clips_basic(tmp_path):
    # Create a small test video using ffmpeg's testsrc (moving pattern)
    vid = tmp_path / "motion.mp4"
    import ffmpeg
    try:
        (
            ffmpeg
            .input("testsrc=duration=6:size=320x240:rate=10", f="lavfi")
            .output(str(vid), vcodec="libx264", pix_fmt="yuv420p", t=6, preset="ultrafast")
            .overwrite_output()
            .run(quiet=True, capture_stderr=True)
        )
    except ffmpeg.Error:
        pytest.skip("ffmpeg failed to generate test video")

    from src.frame_detection.clip_detector import detect_action_clips

    # Compose a simple timeline with one short segment near start
    timeline = [{"start_seconds": 0.5, "end_seconds": 2.5}]

    clips = detect_action_clips(str(vid), timeline, target=3.0)
    assert isinstance(clips, list) and len(clips) == 1
    clip = clips[0]
    assert "start" in clip and "end" in clip
    # sanity checks
    duration = clip["end"] - clip["start"]
    assert 1.9 <= duration <= 4.1
