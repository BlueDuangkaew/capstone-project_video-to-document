import os
from typing import Dict, List
from .video_trimmer import VideoTrimmer


class BatchVideoTrimmer:
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