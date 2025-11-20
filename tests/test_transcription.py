import os
from src.transcription.whisper_transcriber import WhisperTranscriber
from src.transcription.timestamp_aligner import align_transcript_to_video, combine_segment_transcripts
from pathlib import Path

TEST_VIDEO = "tests/sample_video.mp4"  # from earlier; short video
OUTPUT_DIR = "tests/output_transcripts"

def test_transcribe_segment():
    transcriber = WhisperTranscriber(model_name="tiny", output_dir=OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # We expect transcription to run and write a JSON for the video
    res = transcriber.transcribe_segment(TEST_VIDEO, segment_id="testseg")
    assert "segments" in res
    assert Path(f"{OUTPUT_DIR}/testseg.json").exists()

def test_timestamp_align_and_combine():
    # create a fake transcript piece
    sample = {
        "segment_id": "s1",
        "segments": [{"start": 0.0, "end": 1.0, "text": "hello"}]
    }
    aligned = align_transcript_to_video(sample, segment_start_in_video=5.0)
    assert aligned["segments"][0]["start_global"] == 5.0
    combined = combine_segment_transcripts([aligned])
    assert len(combined["combined_segments"]) == 1
    assert combined["combined_segments"][0]["start_global"] == 5.0
