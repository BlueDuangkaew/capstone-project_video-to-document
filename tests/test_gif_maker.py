import os
import shutil
import subprocess
import pytest

from src.utils import gif_maker


def gifski_available():
    return shutil.which("gifski") is not None


@pytest.mark.skipif(not gifski_available(), reason="gifski not installed on host")
def test_make_gif_from_clip(tmp_path):
    # Create a small 3-second test video
    vid = tmp_path / "v.mp4"
    out_gif = tmp_path / "out.gif"

    import ffmpeg

    try:
        (
            ffmpeg
            .input("testsrc=duration=3:size=320x240:rate=15", f="lavfi")
            .output(str(vid), vcodec="libx264", pix_fmt="yuv420p", t=3, preset="ultrafast")
            .overwrite_output()
            .run(quiet=True, capture_stderr=True)
        )
    except ffmpeg.Error:
        pytest.skip("ffmpeg not available")

    # Make the GIF for the 0-2s range
    gif_path = gif_maker.make_gif_from_clip(str(vid), 0.0, 2.0, str(out_gif), fps=10, width=320, quality=80)

    assert os.path.exists(gif_path)
    assert gif_path.endswith(".gif")
    assert os.path.getsize(gif_path) > 0
