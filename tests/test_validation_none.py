import pytest

from src.utils import validation as valmod


def test_get_video_duration_none_raises():
    with pytest.raises(FileNotFoundError):
        valmod.get_video_duration(None)


def test_validate_video_none_returns_problem():
    ok, problems = valmod.validate_video(None)
    assert ok is False
    assert "file_not_found" in problems
