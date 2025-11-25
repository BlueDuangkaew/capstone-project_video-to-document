import os
import json
import tempfile
import ffmpeg
import whisper
from config import config
import datetime
import copy
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm

def format_ts(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    return str(datetime.timedelta(seconds=round(seconds)))

class WhisperTranscriber:
    def __init__(self, model_name: str = None, output_dir: str = "data/transcripts"):
        # If caller doesn't provide a model name, fall back to the centralized
        # configuration (config.WHISPER_MODEL) so the app uses one canonical value.
        # Keep backwards compatibility when a caller explicitly passes model_name.
        # Resolve a safe model name: prefer explicit argument, then config, finally 'small'
        resolved_model = model_name if model_name else (config.WHISPER_MODEL or "small")
        if resolved_model is None or resolved_model == "":
            resolved_model = "small"
        self.model_name = resolved_model

        # Load the model safely (wrap to surface clearer errors if the name is invalid)
        try:
            self.model = whisper.load_model(self.model_name)
        except TypeError as e:
            # Whisper's loader may call os.path functions; raise a clearer exception
            raise RuntimeError(f"Invalid whisper model name: {self.model_name}") from e
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _extract_audio(self, video_path: str, out_audio_path: str) -> str:
        """Extract audio from video to WAV using ffmpeg (mono, 16kHz)."""
        if video_path is None:
            raise FileNotFoundError("video_path is None")

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Input video not found: {video_path}")

        (
            ffmpeg
            .input(video_path)
            .output(out_audio_path, ac=1, ar="16000")
            .overwrite_output()
            .run(quiet=True)
        )
        return out_audio_path

    def transcribe_segment(
        self,
        segment_video_path: str,
        segment_id: str = None,
        language: str = None,
        word_timestamps: bool = False
    ) -> Dict[str, Any]:
        """Transcribe a single video segment and return structured JSON with timestamps."""
        if segment_video_path is None:
            raise FileNotFoundError("segment_video_path is None")

        if not os.path.exists(segment_video_path):
            raise FileNotFoundError(f"segment file not found: {segment_video_path}")

        if segment_id is None:
            segment_id = Path(segment_video_path).stem

        with tempfile.TemporaryDirectory() as td:
            audio_path = os.path.join(td, f"{segment_id}.wav")
            self._extract_audio(segment_video_path, audio_path)

            options: Dict[str, Any] = {}
            if language:
                options["language"] = language
            if word_timestamps:
                options["word_timestamps"] = True

            try:
                result = self.model.transcribe(audio_path, **options)
            except TypeError:
                result = self.model.transcribe(audio_path)

        segments = result.get("segments", [])
        transcript: Dict[str, Any] = {
            "segment_id": segment_id,
            "video_path": segment_video_path,
            "model": self.model_name,
            "duration": result.get("duration"),
            "language": result.get("language", language),
            "raw_text": result.get("text", "").strip(),
            "segments": []
        }

        for seg in segments:
            entry: Dict[str, Any] = {
                "start": format_ts(seg.get("start", 0.0)),
                "end": format_ts(seg.get("end", 0.0)),
                "text": seg.get("text", "").strip(),
                "confidence": seg.get("avg_logprob", None)
            }
            if "words" in seg:
                entry["words"] = seg["words"]
            transcript["segments"].append(entry)

        out_file = self.output_dir / f"{segment_id}.json"
        with open(out_file, "w", encoding="utf-8") as fh:
            json.dump(transcript, fh, ensure_ascii=False, indent=2)

        return transcript

    def transcribe_batch(self, segment_paths: List[str], language: str = None) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for p in tqdm(segment_paths, desc="Transcribing segments"):
            sid = Path(p).stem
            res = self.transcribe_segment(p, segment_id=sid, language=language)
            results.append(res)
        return results
