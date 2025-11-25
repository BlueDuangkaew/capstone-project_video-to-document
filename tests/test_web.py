import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.web import app as web_app


@pytest.fixture(autouse=True)
def disable_pipeline(monkeypatch):
    # Avoid running the heavy background pipeline during tests; replace with no-op
    monkeypatch.setattr("src.web.app.run_pipeline", lambda *a, **k: None)
    yield


def test_api_health():
    client = TestClient(web_app.app)
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_upload_creates_job_file(tmp_path):
    # configure a temporary JOB_DIR to avoid touching system /tmp
    job_dir = tmp_path / "jobs"
    job_dir.mkdir()

    # Monkeypatch the job directory used by the app
    from importlib import reload
    import src.web.app as appmod

    appmod.JOB_DIR = job_dir

    # Monkeypatch validate_video to avoid ffmpeg.probe on dummy bytes
    import src.utils.validation as valmod
    from importlib import reload as _reload
    _reload(valmod)
    import types
    def _fake_validate(path):
        return True, []
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(valmod, "validate_video", _fake_validate)

    client = TestClient(appmod.app)

    file_bytes = b"dummy video data"
    files = {"video": ("example.mp4", file_bytes, "video/mp4")}

    r = client.post("/upload/", files=files)
    assert r.status_code == 200
    body = r.json()
    assert "job_id" in body

    job_file = job_dir / f"{body['job_id']}.json"
    assert job_file.exists()

    data = json.loads(job_file.read_text())
    assert data.get("status") in ("queued", "running")

    monkeypatch.undo()


def test_upload_rejected_on_validation(tmp_path):
    # Ensure invalid uploads are rejected with a 400 and error details
    job_dir = tmp_path / "jobs"
    job_dir.mkdir()

    from importlib import reload
    import src.web.app as appmod

    appmod.JOB_DIR = job_dir

    # Monkeypatch validate_video to return invalid
    import src.utils.validation as valmod
    def _bad_validate(path):
        return False, ["duration_too_long"]

    from fastapi.testclient import TestClient
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(valmod, "validate_video", _bad_validate)

    client = TestClient(appmod.app)
    file_bytes = b"dummy video data"
    files = {"video": ("example.mp4", file_bytes, "video/mp4")}

    r = client.post("/upload/", files=files)
    assert r.status_code == 400
    assert r.json() == {"detail": {"errors": ["duration_too_long"]}}

    monkeypatch.undo()
