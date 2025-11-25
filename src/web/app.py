import json
import uuid
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, Request, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.background import BackgroundTasks

from ..frame_detection.pipeline import extract_frames
from ..transcription.whisper_transcriber import WhisperTranscriber
from ..nlp.pipeline import (
    process_transcript,
    export_to_json,
    export_to_markdown,
    export_to_html,
)
from ..utils.gif_maker import make_gif_from_clip, GifGenerationError
from config import config
from .routes import router as web_router

logger = logging.getLogger(__name__)

app = FastAPI()

# Expose small programmatic API surface for health checks, etc.
app.include_router(web_router, prefix="/api")

# Resolve directories relative to the project root so the app works whether
# it's launched from the repository root or via `python -m src.main`
BASE_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=str(BASE_DIR / "src" / "web" / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "src" / "web" / "static")), name="static")

UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output"
JOB_DIR = Path("/tmp/jobs")

for p in (UPLOAD_DIR, OUTPUT_DIR, JOB_DIR):
    p.mkdir(parents=True, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@app.get("/progress/{job_id}", response_class=HTMLResponse)
def progress(request: Request, job_id: str):
    return templates.TemplateResponse("progress.html", {"request": request, "job_id": job_id})


@app.post("/upload/")
async def upload_video(video: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Upload a video and kick off asynchronous processing.

    This endpoint returns a job id which can be polled via /status/{job_id}
    and the user redirected to /progress/{job_id} for the UI.
    """
    job_id = str(uuid.uuid4())
    safe_name = Path(video.filename).name if video.filename else "upload"
    input_path = UPLOAD_DIR / f"{job_id}_{safe_name}"

    try:
        body = await video.read()
        input_path.write_bytes(body)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to save uploaded file: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    # validate upload (format/duration) and create initial status
    try:
        from ..utils.validation import validate_video

        valid, problems = validate_video(str(input_path))
        if not valid:
            # remove saved file to avoid storing invalid uploads
            try:
                input_path.unlink()
            except Exception:
                pass
            raise HTTPException(status_code=400, detail={"errors": problems})
    except HTTPException:
        # re-raise validation HTTP errors
        raise
    except Exception:
        # If validation unexpectedly fails (missing ffmpeg, rare issues) log and continue
        logger.exception("Validation failed for %s; continuing with upload", input_path)

    # create initial status
    status_path = JOB_DIR / f"{job_id}.json"
    status_path.write_text(json.dumps({"status": "queued", "phase": "Waiting", "progress": 0}))

    # Launch background work
    background_tasks.add_task(run_pipeline, job_id, str(input_path))

    return JSONResponse({"job_id": job_id})


def _write_status(job_id: str, *, status: str, phase: Optional[str] = None, progress: Optional[int] = None):
    p = JOB_DIR / f"{job_id}.json"
    current = {"status": status, "phase": phase or "", "progress": progress or 0}
    try:
        p.write_text(json.dumps(current))
    except Exception:
        logger.exception("Unable to write status file: %s", p)


def run_pipeline(job_id: str, input_path: str):
    """Background task that runs a simplified pipeline and writes status updates.

    For now the implementation is intentionally defensive: each step writes
    a short status update. The pipeline uses available pipeline pieces and
    writes output files under output/{job_id}/
    """
    try:
        _write_status(job_id, status="running", phase="Extracting frames", progress=5)

        # Step 1: extract frames
        output_frames_dir = OUTPUT_DIR / job_id / "frames"
        output_frames_dir.mkdir(parents=True, exist_ok=True)
        extract_frames(input_path, str(output_frames_dir))
        _write_status(job_id, status="running", phase="Transcribing", progress=30)

        # Step 2: transcribe (it's ok if transcription is not available on the host)
        transcriber = WhisperTranscriber(output_dir=str(OUTPUT_DIR / job_id / "transcripts"))
        # Transcribe whole video as a single segment for now
        transcript = transcriber.transcribe_segment(input_path, segment_id=job_id)
        _write_status(job_id, status="running", phase="NLP processing", progress=60)

        # Step 3: NLP processing
        document = process_transcript(transcript, use_llm=False)

        # Step 4: generate GIFs for timeline items and export artifacts
        out_dir = OUTPUT_DIR / job_id
        out_dir.mkdir(parents=True, exist_ok=True)

        # Create gifs output folder
        gifs_dir = out_dir / "gifs"
        gifs_dir.mkdir(parents=True, exist_ok=True)

        # For timeline items, try to create short 2-4s GIFs
        try:
            for idx, item in enumerate(document.get("timeline", [])):
                try:
                    start = float(item.get("start", 0))
                    end = float(item.get("end", start))
                    length = max(0.0, end - start)

                    # Target length between 2 and 4 seconds
                    target = min(max(length, 2.0), 4.0)

                    if length >= target:
                        clip_start = start
                        clip_end = start + target
                    else:
                        extra = (target - length) / 2.0
                        clip_start = max(0.0, start - extra)
                        clip_end = end + extra

                    gif_name = f"gif_{idx:03d}.gif"
                    out_gif = str(gifs_dir / gif_name)

                    # Attempt to make the GIF; this requires gifski to be installed
                    gif_path = make_gif_from_clip(
                        str(input_path),
                        clip_start,
                        clip_end,
                        out_gif,
                        fps=config.GIFSKI_FPS,
                        width=config.GIFSKI_WIDTH,
                        quality=config.GIFSKI_QUALITY,
                    )

                    # store relative path so HTML can reference it
                    item["gif"] = f"gifs/{os.path.basename(gif_path)}"

                except (GifGenerationError, FileNotFoundError) as e:
                    # Do not fail pipeline on gif generation issues; log and continue
                    logger.warning("GIF generation failed for %s: %s", item, e)
                    continue
        except Exception:
            logger.exception("Unexpected GIF generation failure; continuing")

        export_to_json(document, str(out_dir / "documentation.json"))
        export_to_markdown(document, str(out_dir / "documentation.md"))
        export_to_html(document, str(out_dir / "documentation.html"))

        _write_status(job_id, status="completed", phase="Complete", progress=100)

    except Exception as exc:  # pragma: no cover - hard to exercise full pipeline in CI
        logger.exception("Pipeline failed for job %s: %s", job_id, exc)
        _write_status(job_id, status="error", phase=str(exc), progress=0)


@app.get("/status/{job_id}")
def get_status(job_id: str):
    p = JOB_DIR / f"{job_id}.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        return json.loads(p.read_text())
    except Exception as exc:
        logger.exception("Failed to read status for %s: %s", job_id, exc)
        raise HTTPException(status_code=500, detail="Failed to read job status")


@app.get("/result/{job_id}", response_class=HTMLResponse)
def result(request: Request, job_id: str):
    html_path = OUTPUT_DIR / job_id / "documentation.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Result not found")

    preview = html_path.read_text(encoding="utf-8")

    return templates.TemplateResponse("result.html", {"request": request, "job_id": job_id, "preview_html": preview})


@app.get("/download/{job_id}/{filename}")
def download(job_id: str, filename: str):
    path = OUTPUT_DIR / job_id / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(str(path), filename=filename)
