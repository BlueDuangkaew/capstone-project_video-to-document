import ffmpeg
import os
from uuid import uuid4

class VideoTrimmer:
    def __init__(self, output_dir="data/segments"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def trim(self, input_path, start_time, end_time):
        segment_id = uuid4().hex[:8]
        output_file = os.path.join(self.output_dir, f"segment_{segment_id}.mp4")

        (
            ffmpeg
            .input(input_path, ss=start_time, to=end_time)
            .output(output_file, c="copy")
            .overwrite_output()
            .run(quiet=True)
        )
        return output_file

    def detect_scene_changes(self, input_path, threshold=0.4):
        try:
            out, err = (
                ffmpeg
                .input(input_path)
                .filter("select", f"gt(scene,{threshold})")
                .output("pipe:", format="null")
                .global_args("-show_frames")
                .global_args("-print_format", "json")
                .run(capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            print("ffmpeg stderr:", e.stderr.decode())
            raise

        timestamps = []
        for line in err.decode("utf-8").split("\n"):
            if "pts_time" in line:
                try:
                    time_str = line.split("pts_time:")[-1].strip()
                    timestamps.append(float(time_str))
                except ValueError:
                    pass
        return timestamps

    def auto_segment(self, input_path, threshold=0.4, min_length=1.0):
        timestamps = self.detect_scene_changes(input_path, threshold)
        timestamps = [0.0] + timestamps

        probe = ffmpeg.probe(input_path)
        duration = float(probe['format']['duration'])
        timestamps.append(duration)

        segments = []
        for i in range(len(timestamps) - 1):
            start, end = timestamps[i], timestamps[i+1]
            if (end - start) < min_length:
                continue
            output = self.trim(input_path, start, end)
            segments.append(output)
        return segments
