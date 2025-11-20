import subprocess
import os
from datetime import timedelta

def format_timestamp(ts):
    if isinstance(ts, (int, float)):
        return str(timedelta(seconds=ts))
    return ts

def trim_video(input_path, output_path, start_time, end_time, logger):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    cmd = [
        "ffmpeg",
        "-hide_banner", "-loglevel", "error",
        "-ss", format_timestamp(start_time),
        "-to", format_timestamp(end_time),
        "-i", input_path,
        "-c", "copy",
        output_path,
    ]

    logger.info(f"Trimming segment {start_time} -> {end_time} → {output_path}")

    try:
        subprocess.run(cmd, check=True)
        logger.info(f"✔ Saved: {output_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"✘ FFmpeg error for segment {start_time}-{end_time}: {e}")

def batch_trim(input_video, segments, output_dir, logger, progress):
    logger.info(f"Starting batch trim: {len(segments)} segments")

    for seg in segments:
        start = seg["start"]
        end = seg["end"]
        name = seg["name"]

        output_path = os.path.join(output_dir, name)

        trim_video(input_video, output_path, start, end, logger)

        progress.update()
        logger.info(f"Progress: {progress}")
