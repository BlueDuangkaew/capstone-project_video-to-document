import pytest


def test_whisper_init_with_none_model(monkeypatch):
    # Ensure we don't try to load a real model in tests.
    import src.transcription.whisper_transcriber as wt

    class DummyModel:
        def transcribe(self, path, **opts):
            return {"segments": [], "text": "", "duration": 0}

    monkeypatch.setattr("whisper.load_model", lambda name: DummyModel())

    tr = wt.WhisperTranscriber(model_name=None, output_dir="tmp/transcripts")
    assert tr.model_name is not None and tr.model_name != ""


def test_transcribe_segment_raises_on_none(monkeypatch):
    import src.transcription.whisper_transcriber as wt

    class DummyModel:
        def transcribe(self, path, **opts):
            return {"segments": [], "text": "", "duration": 0}

    # Avoid loading a heavy model
    monkeypatch.setattr("whisper.load_model", lambda name: DummyModel())

    tr = wt.WhisperTranscriber(model_name="tiny", output_dir="tmp/transcripts")

    with pytest.raises(FileNotFoundError):
        tr.transcribe_segment(None)
