import ffmpeg
import os
import re
from uuid import uuid4
from typing import List, Tuple, Optional


class VideoTrimmer:
    def __init__(self, output_dir="data/segments"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
    
    def trim(self, input_path: str, start_time: float, end_time: float) -> str:
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        if start_time < 0 or end_time <= start_time:
            raise ValueError(f"Invalid time range: {start_time} to {end_time}")

        segment_id = uuid4().hex[:8]
        output_file = os.path.join(self.output_dir, f"segment_{segment_id}.mp4")

        try:
            (
                ffmpeg
                .input(input_path, ss=start_time, to=end_time)
                .output(output_file, c="copy", avoid_negative_ts="make_zero")
                .overwrite_output()
                .run(quiet=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            if os.path.exists(output_file):
                os.remove(output_file)
            raise RuntimeError(f"FFmpeg error during trimming: {e.stderr.decode()}")

        return output_file

    
    def detect_scene_changes(self, input_path: str, threshold: float = 0.4) -> List[float]:
        """
        Detect scene changes using FFmpeg's scene detection filter.
        
        Args:
            input_path: Path to input video
            threshold: Scene detection threshold (0.0-1.0, default 0.4)
                      Lower = more sensitive (more cuts)
                      Higher = less sensitive (fewer cuts)
        
        Returns:
            List of timestamps (in seconds) where scene changes occur
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        try:
            # Use ffmpeg command line directly for better compatibility
            # The select filter with scene detection writes to stderr
            cmd = [
                "ffmpeg",
                "-i", input_path,
                "-filter:v", f"select='gt(scene,{threshold})',showinfo",
                "-f", "null",
                "-"
            ]
            
            import subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            stderr_text = result.stderr
            
        except Exception as e:
            raise RuntimeError(f"FFmpeg error during scene detection: {e}")
        
        # Parse timestamps from stderr
        # Look for lines like: [Parsed_showinfo_1 @ ...] n:0 pts:xxx pts_time:1.234
        timestamps = []
        
        for line in stderr_text.split("\n"):
            if "Parsed_showinfo" in line and "pts_time:" in line:
                # Extract pts_time value
                match = re.search(r"pts_time:([\d.]+)", line)
                if match:
                    try:
                        timestamps.append(float(match.group(1)))
                    except ValueError:
                        pass
        
        return sorted(timestamps)
    
    def get_duration(self, input_path: str) -> float:
        """Get video duration in seconds."""
        try:
            probe = ffmpeg.probe(input_path)
            return float(probe['format']['duration'])
        except (ffmpeg.Error, KeyError) as e:
            raise RuntimeError(f"Could not get video duration: {e}")
    
    def auto_segment(
        self, 
        input_path: str, 
        threshold: float = 0.4, 
        min_length: float = 1.0,
        max_segments: Optional[int] = None
    ) -> List[str]:
        """
        Automatically segment video at scene changes.
        
        Args:
            input_path: Path to input video
            threshold: Scene detection sensitivity (0.0-1.0)
            min_length: Minimum segment length in seconds
            max_segments: Maximum number of segments to create (None = unlimited)
        
        Returns:
            List of output segment file paths
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Get scene change timestamps
        scene_timestamps = self.detect_scene_changes(input_path, threshold)
        
        # Build segment boundaries
        duration = self.get_duration(input_path)
        boundaries = [0.0] + scene_timestamps + [duration]
        
        # Filter out segments that are too short
        segments = []
        for i in range(len(boundaries) - 1):
            start, end = boundaries[i], boundaries[i + 1]
            
            if (end - start) >= min_length:
                segments.append((start, end))
        
        # Limit segments if requested
        if max_segments and len(segments) > max_segments:
            segments = segments[:max_segments]
        
        # Create segment files
        output_files = []
        for start, end in segments:
            try:
                output_file = self.trim(input_path, start, end)
                output_files.append(output_file)
            except Exception as e:
                print(f"Warning: Failed to create segment {start}-{end}: {e}")
                continue
        
        return output_files
    
    def get_segment_info(self) -> List[Tuple[str, float]]:
        """Get info about all segments in output directory."""
        segments = []
        for filename in os.listdir(self.output_dir):
            if filename.endswith(".mp4"):
                path = os.path.join(self.output_dir, filename)
                try:
                    duration = self.get_duration(path)
                    segments.append((filename, duration))
                except:
                    continue
        return sorted(segments)
