from pathlib import Path
import json
import copy
from typing import Dict, Any, List

def load_transcript_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)

def align_transcript_to_video(transcript: Dict[str, Any], segment_start_in_video: float = 0.0) -> Dict[str, Any]:
    """
    Adjust per-segment timestamps so they are relative to the original full video.
    """
    aligned = copy.deepcopy(transcript)
    for s in aligned.get("segments", []):
        # keep both local and global timestamps
        s["start_global"] = float(segment_start_in_video) + _to_seconds(s["start"])
        s["end_global"] = float(segment_start_in_video) + _to_seconds(s["end"])
    aligned["segment_start_in_video"] = float(segment_start_in_video)
    return aligned

def combine_segment_transcripts(segment_transcripts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge multiple aligned transcripts into one document-level transcript sorted by global time.
    """
    all_segments: List[Dict[str, Any]] = []
    for t in segment_transcripts:
        for s in t.get("segments", []):
            new_s = dict(s)
            new_s["segment_id"] = t.get("segment_id")
            new_s["video_path"] = t.get("video_path")
            all_segments.append(new_s)

    all_segments_sorted = sorted(all_segments, key=lambda x: x.get("start_global", 0.0))
    return {"combined_segments": all_segments_sorted}

def _to_seconds(ts: str) -> float:
    """Convert HH:MM:SS string back to seconds."""
    parts = ts.split(":")
    h, m, s = [int(p) for p in parts]
    return h * 3600 + m * 60 + s
