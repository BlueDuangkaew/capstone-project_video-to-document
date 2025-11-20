from pathlib import Path
import json
from typing import Dict, Any, List

def load_transcript_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)

def align_transcript_to_video(transcript: Dict[str, Any], segment_start_in_video: float = 0.0) -> Dict[str, Any]:
    """
    Adjusts per-segment timestamps so they are relative to the original full video.
    `segment_start_in_video` is the timestamp (seconds) where this segment starts in the full video.
    """
    aligned = dict(transcript)  # shallow copy
    segments = aligned.get("segments", [])
    for s in segments:
        s["start_global"] = float(s["start"]) + float(segment_start_in_video)
        s["end_global"] = float(s["end"]) + float(segment_start_in_video)
    aligned["segment_start_in_video"] = float(segment_start_in_video)
    return aligned

def combine_segment_transcripts(segment_transcripts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge multiple aligned segment transcripts into one document-level transcript sorted by global time.
    """
    all_segments = []
    for t in segment_transcripts:
        for s in t.get("segments", []):
            # carry over parent metadata
            new_s = dict(s)
            new_s["segment_id"] = t.get("segment_id")
            new_s["video_path"] = t.get("video_path")
            all_segments.append(new_s)

    all_segments_sorted = sorted(all_segments, key=lambda x: x.get("start_global", x.get("start", 0.0)))
    return {"combined_segments": all_segments_sorted}
