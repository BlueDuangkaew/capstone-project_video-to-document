"""Video validation helpers.

Provides small helpers to validate an uploaded video file against
project constraints (format, max duration) using existing utilities.
"""
from __future__ import annotations

import os
from typing import List, Tuple

from config import config
import ffmpeg


def is_allowed_format(path: str) -> bool:
    """Return True if the file's extension is in allowed formats.

    This performs a simple extension check and is intended as a first
    validation step during upload.
    """
    ext = os.path.splitext(path)[1].lower().lstrip('.')
    return ext in config.ALLOWED_UPLOAD_FORMATS


def get_video_duration(path: str) -> float:
    """Return the video duration in seconds using ffmpeg probe.

    Raises a RuntimeError if probing fails.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}")
    try:
        probe = ffmpeg.probe(path)
        return float(probe['format']['duration'])
    except Exception as e:
        raise RuntimeError(f"Could not probe video duration: {e}")


def validate_video(path: str) -> Tuple[bool, List[str]]:
    """Validate file path for upload constraints.

    Returns (is_valid, problems) where problems is a list of human readable
    validation messages. Use this at upload time to accept/reject files.
    """
    problems: List[str] = []

    if not os.path.exists(path):
        problems.append("file_not_found")
        return False, problems

    if not is_allowed_format(path):
        problems.append("invalid_format")

    try:
        dur = get_video_duration(path)
    except Exception:
        problems.append("duration_unreadable")
        return False, problems

    if dur > config.MAX_VIDEO_DURATION_SECONDS:
        problems.append("duration_too_long")

    return (len(problems) == 0, problems)
