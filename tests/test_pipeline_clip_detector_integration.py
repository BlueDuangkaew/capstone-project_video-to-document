import os
import json
import tempfile
import pytest

from pathlib import Path


def ffmpeg_available():
    from shutil import which
    return which("ffmpeg") is not None


@pytest.mark.skipif(not ffmpeg_available(), reason="ffmpeg not available")
def test_pipeline_uses_clip_detector_and_generates_docs(tmp_path, monkeypatch):
    # Build a small 5-second test video
    vid = tmp_path / "sample.mp4"
    out_root = tmp_path / "output"
    jobs = tmp_path / "jobs"
    jobs.mkdir()

    import ffmpeg
    try:
        (
            ffmpeg
            .input("testsrc=duration=5:size=320x240:rate=10", f="lavfi")
            .output(str(vid), vcodec="libx264", pix_fmt="yuv420p", t=5, preset="ultrafast")
            .overwrite_output()
            .run(quiet=True, capture_stderr=True)
        )
    except ffmpeg.Error:
        pytest.skip("ffmpeg not available")

    import src.web.app as appmod

    # Configure app to use our tmp dirs
    appmod.OUTPUT_DIR = out_root
    appmod.JOB_DIR = jobs


    # Replace WhisperTranscriber with a dummy that returns a simple transcript
    class DummyTranscriber:
        def __init__(self, output_dir=None):
            pass

        def transcribe_segment(self, input_path, segment_id=None):
            return {
                "segment_id": segment_id or "test",
                "segments": [
                    {"start_seconds": 0, "end_seconds": 2, "text": "Step one", "label": "action", "segment_index": 0},
                ],
                "duration": 5,
                "model": "test",
                "language": "en",
                "video_path": input_path,
            }

    monkeypatch.setattr(appmod, "WhisperTranscriber", DummyTranscriber)

    # Replace process_transcript to return a document with a timeline item
    def fake_process_transcript(transcript, use_llm=False, model=None):
        # Provide a timeline such that clip detector can choose a clip
        return {
            "video_id": transcript.get("segment_id", "test"),
            "title": "Test",
            "summary": "summary",
            "steps": ["Step one"],
            "timeline": [
                {"start_seconds": 0.0, "end_seconds": 2.0, "start_formatted": "0:00", "end_formatted": "0:02", "text": "Step one", "label": "action"}
            ],
            "statistics": {"total_segments": 1, "total_words": 2},
            "metadata": {"duration": 5},
        }

    monkeypatch.setattr(appmod, "process_transcript", fake_process_transcript)

    # Monkeypatch GIF maker to produce a dummy gif file without gifski
    def fake_make_gif(input_video, start, end, out_path, fps=None, width=None, quality=None):
        # ensure out directory exists
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "wb") as fh:
            fh.write(b"GIF89a")
        return out_path

    monkeypatch.setattr(appmod, "make_gif_from_clip", fake_make_gif)

    # Run pipeline and verify outputs
    job_id = "job-test-clip"
    appmod.run_pipeline(job_id, str(vid))

    out_job_dir = out_root / job_id
    assert out_job_dir.exists()

    gifs_dir = out_job_dir / "gifs"
    assert gifs_dir.exists(), "gifs directory should exist"

    gifs = list(gifs_dir.glob("*.gif"))
    assert len(gifs) > 0, "At least one gif should have been created"

    # documentation.html should reference the gif via the app download URL
    html_path = out_job_dir / "documentation.html"
    assert html_path.exists()
    content = html_path.read_text(encoding="utf-8")
    assert f"/download/{job_id}/gifs/" in content

    # documentation.json should carry created_gifs metadata
    json_path = out_job_dir / "documentation.json"
    assert json_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert "created_gifs" in data.get("metadata", {})
    assert len(data["metadata"]["created_gifs"]) > 0
