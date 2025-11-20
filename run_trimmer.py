from src.trimmer.video_trimmer import VideoTrimmer

trimmer = VideoTrimmer("data/output/segments")

# Manual trim
# segment = trimmer.trim("data/input_videos/sample_video.mp4", start_time=10, end_time=20)
# print(f"Created: {segment}")

# Auto segment with scene detection
segments = trimmer.auto_segment(
    "data/input_videos/sample_video.mp4",
    threshold=0.4,      # 0.0-1.0, lower = more cuts
    min_length=2.0,     # Skip segments shorter than 2s
    max_segments=None     # Limit output (optional)
)

print(f"Created {len(segments)} segments")