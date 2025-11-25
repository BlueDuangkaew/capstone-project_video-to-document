"""Batch video trimming helpers.

This module provides `BatchVideoTrimmer`, a small helper class that
wraps `VideoTrimmer` to process all videos in an input directory
and produce trimmed segments into an output directory.

Usage
-----
Programmatic example:

        from src.trimmer.batch_video_trimmer import BatchVideoTrimmer

        # Create with optional paths (defaults shown)
        bvt = BatchVideoTrimmer(input_dir="data/input_videos",
                                                     output_dir="data/segments")

        # Process all files in the input directory
        results = bvt.process_all(threshold=0.4, min_length=1.0, verbose=True)

        # Get a concise summary of the run
        summary = bvt.get_summary(results)

Per-file processing example:

        segments = bvt.process_single("example.mp4", threshold=0.35)

Notes
-----
- `input_dir` should contain video files in supported formats
    (mp4, mov, mkv, avi, webm, flv). The method `get_video_files`
    performs a case-insensitive suffix check.
- `VideoTrimmer` (imported from `.video_trimmer`) performs the actual
    segmentation/trimming. Ensure any dependencies used by `VideoTrimmer`
    (for example `ffmpeg` or python packages) are installed. See
    `requirements.txt` for Python deps.
- `process_all` returns a dict with per-file status and segment lists.
    On error the `error` field contains the exception message.

Return format (per file):

        {
                "status": "success" | "error",
                "segments": [...paths to segments...] | None,
                "error": "error message" | None,
                "segment_count": int
        }

"""

import os
from typing import Dict, List
from .video_trimmer import VideoTrimmer


class BatchVideoTrimmer:
    """Batch-process videos in a directory using `VideoTrimmer`.

    This class discovers video files in `input_dir` (by extension),
    calls `VideoTrimmer.auto_segment` for each file, and aggregates
    results. Methods provided:

    - `get_video_files()` -> list of filenames found in `input_dir`.
    - `process_all(...)` -> dict mapping filename -> result dict.
    - `process_single(filename, ...)` -> list of produced segment paths.
    - `get_summary(results)` -> aggregate statistics for a batch run.

    Implementation notes:
    - The trimmer instance is created with `output_dir` and is reused
      for each file processed.
    - `process_all` catches exceptions per-file and records the
      exception message in the returned results; it does not raise
      on the first error.
    """
    def __init__(self, input_dir="data/input_videos", output_dir="data/segments"):
        self.input_dir = input_dir
        self.trimmer = VideoTrimmer(output_dir)

        # Create input directory if it doesn't exist
        os.makedirs(self.input_dir, exist_ok=True)

    def get_video_files(self) -> List[str]:
        """Get all video files from input directory."""
        supported_formats = (".mp4", ".mov", ".mkv", ".avi", ".webm", ".flv")
        
        if not os.path.exists(self.input_dir):
            return []
        
        files = [
            f for f in os.listdir(self.input_dir) 
            if f.lower().endswith(supported_formats)
        ]
        return sorted(files)
    
    def process_all(
        self, 
        threshold: float = 0.4, 
        min_length: float = 1.0,
        verbose: bool = True
    ) -> Dict[str, Dict]:
        """
        Process all videos in input directory.
        
        Args:
            threshold: Scene detection sensitivity
            min_length: Minimum segment length in seconds
            verbose: Print progress messages
        
        Returns:
            Dictionary mapping filenames to results:
            {
                "filename.mp4": {
                    "status": "success" | "error",
                    "segments": [...] | None,
                    "error": error_message | None
                }
            }
        """
        files = self.get_video_files()
        
        if not files:
            if verbose:
                print(f"No video files found in {self.input_dir}")
            return {}
        
        if verbose:
            print(f"Found {len(files)} video(s) to process")
        
        results = {}
        
        for idx, filename in enumerate(files, 1):
            full_path = os.path.join(self.input_dir, filename)
            
            if verbose:
                print(f"[{idx}/{len(files)}] Processing: {filename}")
            
            try:
                segments = self.trimmer.auto_segment(
                    full_path, 
                    threshold=threshold, 
                    min_length=min_length
                )
                
                results[filename] = {
                    "status": "success",
                    "segments": segments,
                    "error": None,
                    "segment_count": len(segments)
                }
                
                if verbose:
                    print(f"  ✓ Created {len(segments)} segment(s)")
                    
            except Exception as e:
                results[filename] = {
                    "status": "error",
                    "segments": None,
                    "error": str(e),
                    "segment_count": 0
                }
                
                if verbose:
                    print(f"  ✗ Error: {e}")
        
        return results
    
    def process_single(
        self, 
        filename: str, 
        threshold: float = 0.4, 
        min_length: float = 1.0
    ) -> List[str]:
        """
        Process a single video file.
        
        Args:
            filename: Name of file in input_dir
            threshold: Scene detection sensitivity
            min_length: Minimum segment length
        
        Returns:
            List of output segment paths
        """
        full_path = os.path.join(self.input_dir, filename)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {full_path}")
        
        return self.trimmer.auto_segment(
            full_path, 
            threshold=threshold, 
            min_length=min_length
        )
    
    def get_summary(self, results: Dict[str, Dict]) -> Dict:
        """Generate summary statistics from batch results."""
        total = len(results)
        successful = sum(1 for r in results.values() if r["status"] == "success")
        failed = total - successful
        total_segments = sum(r["segment_count"] for r in results.values())
        
        return {
            "total_videos": total,
            "successful": successful,
            "failed": failed,
            "total_segments": total_segments,
            "success_rate": f"{(successful/total*100):.1f}%" if total > 0 else "0%"
        }