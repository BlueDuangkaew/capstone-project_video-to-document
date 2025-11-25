import json
from pathlib import Path


def test_run_pipeline_writes_error_status(tmp_path, monkeypatch):
    # Create dummy input video file
    vid = tmp_path / "bad.mp4"
    vid.write_bytes(b"hello")

    out_root = tmp_path / "output"
    jobs = tmp_path / "jobs"
    jobs.mkdir()

    import src.web.app as appmod

    # Monkeypatch directories
    appmod.OUTPUT_DIR = out_root
    appmod.JOB_DIR = jobs

    # Monkeypatch WhisperTranscriber to raise during transcription
    class BrokenTranscriber:
        def __init__(self, output_dir=None):
            pass

        def transcribe_segment(self, input_path, segment_id=None):
            raise RuntimeError("transcription failed")

    monkeypatch.setattr(appmod, "WhisperTranscriber", BrokenTranscriber)

    job_id = "job-error"
    # Run pipeline which should catch exception and write an error status file
    appmod.run_pipeline(job_id, str(vid))

    status_file = jobs / f"{job_id}.json"
    assert status_file.exists()
    data = json.loads(status_file.read_text())
    assert data.get("status") == "error"
    assert "transcription failed" in data.get("error_message", "")
    assert "Traceback" in data.get("error_trace", "")


def test_error_page_renders(monkeypatch, tmp_path):
    # Setup a fake status file and verify the /error route returns html with details
    job_id = "job-err-page"
    job_dir = tmp_path / "jobs"
    job_dir.mkdir()
    status = {"status": "error", "phase": "Transcribing", "progress": 0, "error_message": "boom", "error_trace": "stacktrace"}
    (job_dir / f"{job_id}.json").write_text(json.dumps(status))

    import importlib
    import src.web.app as appmod
    appmod.JOB_DIR = job_dir

    from fastapi.testclient import TestClient
    client = TestClient(appmod.app)

    r = client.get(f"/error/{job_id}")
    assert r.status_code == 200
    assert "boom" in r.text
    assert "Transcribing" in r.text
