import pytest

from pathlib import Path


def ffmpeg_available():
    from shutil import which
    return which("ffmpeg") is not None


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg not available")
def test_clip_detector_prefers_ocr_timestamp(tmp_path, monkeypatch):
    # Create a simple test video
    vid = tmp_path / "ocr_motion.mp4"
    import ffmpeg

    try:
        (
            ffmpeg
            .input("testsrc=duration=8:size=320x240:rate=10", f="lavfi")
            .output(str(vid), vcodec="libx264", pix_fmt="yuv420p", t=8, preset="ultrafast")
            .overwrite_output()
            .run(quiet=True, capture_stderr=True)
        )
    except ffmpeg.Error:
        pytest.skip("ffmpeg not available")

    # We will monkeypatch the low-level OCR detector to pretend text is
    # present at timestamps near 5.0s. This should bias the detector to
    # select a clip that includes 5.0s rather than the naive center.

    from src.frame_detection import clip_detector as cd

    def fake_detect_text_in_frame(frame):
        # The clip_detector samples frames at fixed timestamps; we don't
        # have access to the actual timestamp here, but the detector's
        # algorithm relies on _detect_text_in_frame called within
        # _find_motion_peak. We will toggle return values based on a
        # global switching counter stored on the function object.
        # The patched function will return True the 5th and 6th time it's
        # called (simulating OCR at ~5s in our sampling). This approach is
        # deterministic for our test video.
        if not hasattr(fake_detect_text_in_frame, "count"):
            fake_detect_text_in_frame.count = 0
        fake_detect_text_in_frame.count += 1
        # Mark frames corresponding to timestamps around 5s in a 1->6s
        # sampling window: approximately the 9th and 10th sampled frames.
        return fake_detect_text_in_frame.count in (9, 10)

    monkeypatch.setattr(cd, "_detect_text_in_frame", fake_detect_text_in_frame)

    # Provide a timeline entry around 3-4s so the padded scan window will
    # cover later timestamps (~5s) where we simulate OCR
    timeline = [{"start_seconds": 3.0, "end_seconds": 4.0}]

    # First, run without OCR present so we have a baseline
    monkeypatch.setattr(cd, "_detect_text_in_frame", lambda frame: False)
    baseline_clips = cd.detect_action_clips(str(vid), timeline, target=3.0, ocr_weight=0.0)
    baseline_mid = (baseline_clips[0]["start"] + baseline_clips[0]["end"]) / 2.0

    # Now run with simulated OCR positives later in the window
    fake_detect_text_in_frame.count = 0
    monkeypatch.setattr(cd, "_detect_text_in_frame", fake_detect_text_in_frame)
    clips = cd.detect_action_clips(str(vid), timeline, target=3.0, ocr_weight=200.0)
    assert isinstance(clips, list) and len(clips) == 1
    clip = clips[0]

    # The presence of OCR later in the window should pull the chosen
    # clip's midpoint forward (towards the OCR-positive timestamps).
    mid = (clip["start"] + clip["end"]) / 2.0
    assert mid > baseline_mid, "OCR-positive frames should bias clip selection towards later timestamps"
