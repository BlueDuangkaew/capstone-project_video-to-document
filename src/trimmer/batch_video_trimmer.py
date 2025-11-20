import os
from .video_trimmer import VideoTrimmer

class BatchVideoTrimmer:
    def __init__(self, input_dir="data/input_videos", output_dir="data/segments"):
        self.input_dir = input_dir
        self.trimmer = VideoTrimmer(output_dir)

    def process_all(self):
        files = [f for f in os.listdir(self.input_dir) if f.endswith((".mp4", ".mov", ".mkv"))]
        results = {}

        for f in files:
            full_path = os.path.join(self.input_dir, f)
            segments = self.trimmer.auto_segment(full_path)
            results[f] = segments

        return results
