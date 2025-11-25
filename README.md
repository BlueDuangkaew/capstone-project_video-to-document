# Video to Polished Documentation

Convert instructional videos into clean, step-by-step HTML documentation, powered by GIFs.

This repository contains a platform that lets organizations upload an instructional video (maximum length: 15 minutes) and automatically produces a GIF-powered HTML instructional document. The system focuses on producing small, high-quality GIFs of short 2–4 second clips that demonstrate each step.

## Goals and features (overview)
- Enforce an upload duration limit of 15 minutes (reject or require trimming if exceeded).
- Event-based clip detection (2–4s clips) rather than single frames.
- Use gifski to generate smooth, compact GIFs for each step.
- Align clips to text (via embedding models, OCR hints, motion context) to map one clip per instruction step.
- Produce a responsive, GIF-embedded HTML document as the final output (PDF export optional).
- Web interface for upload, trimming, preview and download.

## Tech & tools
- Python, FastAPI (backend)
- OpenCV (video processing, clipping, trimming)
- FFmpeg (low-level trimming/clip extraction)
- gifski (high-quality GIF generation)
	- gifski (high-quality GIF generation) — required for GIF output; see `docs/install.md` for install instructions and Docker support.
- Whisper / other ASR for transcription
- CLIP-like models for clip-text alignment
- OCR for visual hints
- Frontend: simple responsive HTML and JS for preview and download
- Docker (optional)
- Docker (optional) — see `docs/install.md` and `docker/Dockerfile` for an example container that installs ffmpeg and gifski.

## Processing pipeline (high-level)

1. Upload + validation
	- Backend checks format (MP4/MOV/WebM) and duration ≤ 15 minutes.
	- If video is longer, reject the upload or require trimming.

2. Optional trimming
	- If user supplies segments or after auto-detection, trim segments using OpenCV/FFmpeg.
	- Each segment must still satisfy the ≤ 15 minute rule.

3. Event-based clip detection
	- Detect short 2–4s clips where meaningful actions happen using frame differencing / SSIM / histograms and UI cues such as cursor movement or transitions.

4. Clip–text alignment
	- Align textual steps to the best matching clip using visual embeddings, OCR hints, and motion context.

5. GIF generation
	- Extract short MP4 clips and convert them to optimized GIFs using gifski.
	- Aim for high visual quality at small size (~100–300 KB per GIF) using gifski fine-tuning.

6. HTML document builder
	- Build a clean responsive HTML document with GIFs and step text.

## Development Setup

Quickstart (local development):

1. Create virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Run tests:

```bash
pytest
```

3. Start the web UI (development reload mode):

```bash
python -m src.main --reload
```

4. Example scripts are under `examples/` (moved from the repository root to keep the project tidy):

```bash
python examples/run_trimmer.py
python examples/run_nlp_pipeline.py
```

Makefile helpers:

```bash
make install   # create venv and install requirements
make test      # run tests
make serve     # start app using src.main

## Notes and next steps
- A design doc lives in `docs/architecture.md` (added to this repo) with component details, gifski usage, expected sizing, and an example HTML structure.
- `config.py` now contains constants and thresholds used across the pipeline (duration, formats, gifski settings).
```
