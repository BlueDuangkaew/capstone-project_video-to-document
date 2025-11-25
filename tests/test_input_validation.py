import json
import os
import pytest

from pathlib import Path


def test_run_pipeline_reports_missing_input(tmp_path):
    import src.web.app as appmod

    job_dir = tmp_path / "jobs"
    job_dir.mkdir()
    appmod.JOB_DIR = job_dir

    job_id = "missing-input"
    # Call with None -> should write an error status file and return cleanly
    appmod.run_pipeline(job_id, None)

    status_file = job_dir / f"{job_id}.json"
    assert status_file.exists()
    data = json.loads(status_file.read_text())
    assert data.get("status") == "error"
    assert "input_path is None" in data.get("error_message", "")


def test_make_gif_from_clip_raises_on_none():
    from src.utils.gif_maker import make_gif_from_clip

    with pytest.raises(FileNotFoundError):
        make_gif_from_clip(None, 0, 1, "/tmp/out.gif")


def test_video_trimmer_raises_on_none():
    from src.trimmer.video_trimmer import VideoTrimmer

    vt = VideoTrimmer(output_dir=str(Path("/tmp/segments_test")))

    with pytest.raises(FileNotFoundError):
        vt.trim(None, 0.0, 1.0)