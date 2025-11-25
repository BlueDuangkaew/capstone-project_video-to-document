"""GIF generation helper using FFmpeg + gifski.

This module provides a small helper to extract a short clip from a
video file (using ffmpeg) and then convert it into a high-quality GIF
using the gifski binary. The function is conservative and returns
clear exceptions when the required tools are missing.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import ffmpeg

from config import config


class GifGenerationError(RuntimeError):
    pass


def _check_gifski_available() -> bool:
    return shutil.which("gifski") is not None


def make_gif_from_clip(
    input_video: str,
    start_time: float,
    end_time: float,
    output_gif: str,
    fps: Optional[int] = None,
    width: Optional[int] = None,
    quality: Optional[int] = None,
) -> str:
    """Create a GIF for a short clip between start_time and end_time.

    Steps:
    1. Create a temporary directory and extract frames from the requested
       clip using ffmpeg at `fps` frames per second into PNG files.
    2. Call gifski to convert the PNG sequence into a GIF.

    Returns the path to the output GIF on success.

    Raises GifGenerationError on failure.
    """
    if not os.path.exists(input_video):
        raise FileNotFoundError(f"Input video not found: {input_video}")

    if fps is None:
        fps = config.GIFSKI_FPS
    if quality is None:
        quality = config.GIFSKI_QUALITY

    if not _check_gifski_available():
        raise GifGenerationError("gifski binary not found on PATH; please install gifski to use this feature")

    output_gif_path = Path(output_gif)
    output_gif_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Compose ffmpeg command to extract frames to tmpdir/frame%04d.png
        frame_pattern = os.path.join(tmpdir, "frame%04d.png")

        try:
            stream = (
                ffmpeg
                .input(input_video, ss=start_time, to=end_time)
                .filter('fps', fps=fps)
                .output(frame_pattern, start_number=0, pix_fmt='rgb24', vframes=9999)
                .overwrite_output()
            )
            stream.run(quiet=True, capture_stderr=True)
        except ffmpeg.Error as e:
            raise GifGenerationError(f"ffmpeg failed to extract frames: {getattr(e, 'stderr', str(e))}")

        # Build gifski command
        cmd = ["gifski", "-o", str(output_gif_path), os.path.join(tmpdir, "frame*.png")]
        if width:
            cmd.extend(["--width", str(width)])
        if quality:
            cmd.extend(["--quality", str(quality)])

        try:
            # Using shell for glob expansion is simplest and OK for a local tool
            subprocess.run(" ".join(cmd), shell=True, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise GifGenerationError(f"gifski failed: {e.stderr.decode(errors='ignore')}")

    if not output_gif_path.exists():
        raise GifGenerationError("Expected GIF output not created")

    return str(output_gif_path)
