"""
Example usage for the trimmer pipeline (moved into examples/ for tidiness).
"""

from src.trimmer.video_trimmer import VideoTrimmer
from pathlib import Path

def main():
    trimmer = VideoTrimmer("data/output/segments")
    video = Path("data/input_videos/sample_video.mp4")
    if not video.exists():
        print("sample video not found", video)
        return

    segments = trimmer.auto_segment(str(video), threshold=0.4, min_length=2.0)
    print(f"Created {len(segments)} segments")

if __name__ == "__main__":
    main()
