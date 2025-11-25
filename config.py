"""Application configuration.

This module loads configuration from the environment (and a `.env`
file when present) and exposes a `config` object with convenient
Path-backed attributes. Paths are converted to `pathlib.Path` and
created on initialization so other parts of the code can rely on them
existing.
"""

from __future__ import annotations

from dataclasses import dataclass
from dotenv import load_dotenv
import os
from pathlib import Path
from typing import Optional


load_dotenv()


@dataclass
class Config:
    """Typed configuration container.

    Values are read from environment variables with sensible defaults.
    """
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "small")
    LLAMA_MODEL: Optional[str] = os.getenv("LLAMA_MODEL")

    # Directory where uploaded/input videos live (default: data/input_videos)
    UPLOAD_PATH: Path = Path(os.getenv("UPLOAD_PATH", "data/input_videos"))

    # Directory where generated segments are written (default: data/segments)
    SEGMENTS_PATH: Path = Path(os.getenv("SEGMENTS_PATH", "data/segments"))

    # Directory for logs
    LOG_PATH: Path = Path(os.getenv("LOG_PATH", "output/logs"))

    # General purpose debug flag
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")
    # Maximum allowed duration for input video in seconds (15 minutes = 900 seconds)
    MAX_VIDEO_DURATION_SECONDS: int = int(os.getenv("MAX_VIDEO_DURATION_SECONDS", "900"))

    # Allowed upload formats
    ALLOWED_UPLOAD_FORMATS: tuple = tuple(os.getenv("ALLOWED_UPLOAD_FORMATS", "mp4,mov,webm").split(","))

    # gifski tuning options (passed to gifski/command-line wrapper or used by wrapper)
    GIFSKI_FPS: int = int(os.getenv("GIFSKI_FPS", "15"))
    GIFSKI_WIDTH: Optional[int] = None if os.getenv("GIFSKI_WIDTH") in (None, "") else int(os.getenv("GIFSKI_WIDTH"))
    GIFSKI_QUALITY: int = int(os.getenv("GIFSKI_QUALITY", "80"))

    def __post_init__(self) -> None:
        # Ensure Path types and create directories used by the app
        self.UPLOAD_PATH = Path(self.UPLOAD_PATH)
        self.SEGMENTS_PATH = Path(self.SEGMENTS_PATH)
        self.LOG_PATH = Path(self.LOG_PATH)

        for p in (self.UPLOAD_PATH, self.SEGMENTS_PATH, self.LOG_PATH):
            try:
                p.mkdir(parents=True, exist_ok=True)
            except Exception:
                # If directory creation fails, do not crash import time; callers
                # that rely on the directories can handle the failure.
                pass


config = Config()
