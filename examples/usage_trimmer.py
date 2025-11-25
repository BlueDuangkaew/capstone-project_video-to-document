"""Example usage for the trimmer utilities.

This script demonstrates basic programmatic usage of:
- `src.trimmer.video_trimmer.VideoTrimmer`
- `src.trimmer.batch_video_trimmer.BatchVideoTrimmer`

Prerequisites
-------------
- Install Python dependencies: `pip install -r requirements.txt`
- Install system `ffmpeg` binary and ensure it is on your `PATH`.

Run examples from the project root so that `src` is importable, e.g.:

    cd /home/booblue/capstone-project
    python examples/usage_trimmer.py --single data/input_videos/example.mp4

Or run the batch example:

    python examples/usage_trimmer.py --batch

Note: You can also set `PYTHONPATH=.` to run from elsewhere.
"""

import argparse
import pprint
import os

from src.trimmer.video_trimmer import VideoTrimmer
from src.trimmer.batch_video_trimmer import BatchVideoTrimmer
from config import config as project_config


def single_example(input_path: str, out_dir: str = "data/segments"):
    """Trim one video by automatically detecting scene changes.

    Prints the list of created segment file paths.
    """
    vt = VideoTrimmer(output_dir=out_dir)

    print(f"Auto-segmenting: {input_path}")
    segments = vt.auto_segment(input_path, threshold=0.4, min_length=1.0)

    print("Created segments:")
    pprint.pprint(segments)


def batch_example(input_dir: str = None, out_dir: str = "data/segments"):
    """Process all videos found in `input_dir` and print a summary.

    If `input_dir` is None the value from `config.config.UPLOAD_PATH` is used.
    """
    if input_dir is None:
        input_dir = project_config.UPLOAD_PATH
    """Process all videos found in `input_dir` and print a summary."""
    bvt = BatchVideoTrimmer(input_dir=input_dir, output_dir=out_dir)

    files = bvt.get_video_files()
    print(f"Found {len(files)} video(s) in {input_dir}: {files}")

    results = bvt.process_all(threshold=0.4, min_length=1.0, verbose=True)
    print("Batch results:")
    pprint.pprint(results)

    summary = bvt.get_summary(results)
    print("Summary:")
    pprint.pprint(summary)


def main():
    parser = argparse.ArgumentParser(description="Usage examples for trimmer utilities")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--single", help="Path to a single video file to auto-segment")
    group.add_argument("--batch", action="store_true", help="Process all videos in the configured input directory")
    parser.add_argument("--input-dir", default=None, help="Override the configured input directory")
    parser.add_argument("--out", default="data/segments", help="Output directory for segments")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    if args.single:
        single_example(args.single, args.out)
    elif args.batch:
        batch_example(input_dir=args.input_dir, out_dir=args.out)


if __name__ == "__main__":
    main()
