import os
import json
from pathlib import Path
from src.transcription.whisper_transcriber import WhisperTranscriber
from src.transcription.timestamp_aligner import align_transcript_to_video, combine_segment_transcripts

TEST_VIDEO = "data/input_videos/sample_video.mp4"
OUTPUT_DIR = "data/output/transcripts"

def test_transcribe_segment():
    transcriber = WhisperTranscriber(model_name="tiny", output_dir=OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    res = transcriber.transcribe_segment(TEST_VIDEO, segment_id="testseg")
    assert "segments" in res
    assert len(res["segments"]) > 0
    out_file = Path(OUTPUT_DIR) / "testseg.json"
    assert out_file.exists()
    with open(out_file, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    # Check timestamp format
    assert isinstance(data["segments"][0]["start"], str)
    assert ":" in data["segments"][0]["start"]

def test_timestamp_align_and_combine():
    sample = {
        "segment_id": "s1",
        "video_path": "vid.mp4",
        "segments": [{"start": "00:00:00", "end": "00:00:01", "text": "hello"}]
    }
    aligned = align_transcript_to_video(sample, segment_start_in_video=5.0)
    assert aligned["segments"][0]["start_global"] == 5.0
    combined = combine_segment_transcripts([aligned])
    assert len(combined["combined_segments"]) == 1
    assert combined["combined_segments"][0]["start_global"] == 5.0
