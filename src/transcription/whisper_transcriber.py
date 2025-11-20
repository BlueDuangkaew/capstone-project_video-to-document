import os
import json
import tempfile
import ffmpeg
import whisper
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm

class WhisperTranscriber:
    def __init__(self, model_name: str = "small", output_dir: str = "data/transcripts"):
        self.model_name = model_name
        self.model = whisper.load_model(model_name)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _extract_audio(self, video_path: str, out_audio_path: str):
        """
        Extracts audio from video to a WAV/MP3 file using ffmpeg.
        """
        (
            ffmpeg
            .input(video_path)
            .output(out_audio_path, ac=1, ar="16000")  # mono, 16kHz
            .overwrite_output()
            .run(quiet=True)
        )
        return out_audio_path

    def transcribe_segment(self, segment_video_path: str, segment_id: str = None,
                           language: str = None, word_timestamps: bool = False) -> Dict[str, Any]:
        """
        Transcribe a single video segment and return a JSON-like dict with timestamps.
        Uses whisper.transcribe which provides word-level timestamps if using newer whisper versions.
        """
        if segment_id is None:
            segment_id = Path(segment_video_path).stem

        with tempfile.TemporaryDirectory() as td:
            audio_path = os.path.join(td, f"{segment_id}.wav")
            self._extract_audio(segment_video_path, audio_path)

            # use Whisper's transcribe interface
            # set word_timestamps=True if model version supports it
            options = {"language": language} if language else {}
            # newer whisper (openai-whisper) supports task and word_timestamps flags
            try:
                result = self.model.transcribe(audio_path, **options)
            except TypeError:
                # fallback for older API signatures
                result = self.model.transcribe(audio_path)

        # Build structured transcript entries
        # Whisper result typically contains 'segments' with start/end/text
        segments = result.get("segments", [])
        transcript = {
            "segment_id": segment_id,
            "video_path": segment_video_path,
            "model": self.model_name,
            "duration": result.get("duration"),
            "language": result.get("language", language),
            "raw_text": result.get("text", "").strip(),
            "segments": []
        }

        for seg in segments:
            transcript_entry = {
                "start": float(seg.get("start", 0.0)),
                "end": float(seg.get("end", 0.0)),
                "text": seg.get("text", "").strip(),
                "confidence": seg.get("avg_logprob", None)  # not always present
            }
            # If word-level timestamps exist, attach them
            if "words" in seg:
                transcript_entry["words"] = seg["words"]
            transcript["segments"].append(transcript_entry)

        # Save JSON to output_dir
        out_file = self.output_dir / f"{segment_id}.json"
        with open(out_file, "w", encoding="utf-8") as fh:
            json.dump(transcript, fh, ensure_ascii=False, indent=2)

        return transcript

    def transcribe_batch(self, segment_paths: List[str], language: str = None) -> List[Dict[str, Any]]:
        results = []
        for p in tqdm(segment_paths, desc="Transcribing segments"):
            sid = Path(p).stem
            res = self.transcribe_segment(p, segment_id=sid, language=language)
            results.append(res)
        return results
