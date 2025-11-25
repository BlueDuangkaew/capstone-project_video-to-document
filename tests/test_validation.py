import os
import shutil
import pytest

from src.utils import validation


def test_is_allowed_format_positive():
    assert validation.is_allowed_format("video.mp4")
    assert validation.is_allowed_format("VIDEO.MOV")


def test_is_allowed_format_negative():
    assert not validation.is_allowed_format("document.txt")


def test_validate_video_success(tmp_path, monkeypatch):
    # Create a tiny test video with ffmpeg similar to other tests
    test_video = tmp_path / "tiny.mp4"

    import ffmpeg
    # Create a 2-second color test video
    try:
        (
            ffmpeg
            .input("testsrc=duration=2:size=320x240:rate=15", f="lavfi")
            .output(str(test_video), vcodec="libx264", pix_fmt="yuv420p", t=2, preset="ultrafast")
            .overwrite_output()
            .run(quiet=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        pytest.skip("ffmpeg not available for creating test video")

    valid, problems = validation.validate_video(str(test_video))
    assert valid
    assert problems == []


def test_validate_video_duration_too_long(tmp_path, monkeypatch):
    test_video = tmp_path / "dummy.mp4"
    test_video.write_text("dummy")

    # Monkeypatch get_video_duration to return > 900
    monkeypatch.setattr(validation, "get_video_duration", lambda p: 901.0)

    valid, problems = validation.validate_video(str(test_video))
    assert not valid
    assert "duration_too_long" in problems
