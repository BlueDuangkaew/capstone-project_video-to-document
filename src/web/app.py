import os, uuid, json, subprocess
from fastapi import FastAPI, UploadFile, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.background import BackgroundTasks

app = FastAPI()

templates = Jinja2Templates(directory="src/web/templates")

app.mount("/static", StaticFiles(directory="src/web/static"), name="static")

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output"
JOB_DIR = "/tmp/jobs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(JOB_DIR, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@app.get("/progress/{job_id}", response_class=HTMLResponse)
def progress(request: Request, job_id: str):
    return templates.TemplateResponse("progress.html", {"request": request, "job_id": job_id})


@app.post("/upload/")
async def upload_video(file: UploadFile, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    input_path = f"{UPLOAD_DIR}/{job_id}_{file.filename}"

    with open(input_path, "wb") as f:
        f.write(await file.read())

    # create initial status
    json.dump({"status": "queued", "phase": "Waiting", "progress": 0},
              open(f"{JOB_DIR}/{job_id}.json", "w"))

    background_tasks.add_task(run_pipeline, job_id, input_path)

    return {"job_id": job_id}


def run_pipeline(job_id: str, input_path: str):
    cmd = ["python", "run.py", "--input", input_path, "--job-id", job_id]
    subprocess.run(cmd)


@app.get("/status/{job_id}")
def get_status(job_id: str):
    return json.load(open(f"{JOB_DIR}/{job_id}.json"))


@app.get("/result/{job_id}", response_class=HTMLResponse)
def result(request: Request, job_id: str):
    html_path = f"{OUTPUT_DIR}/{job_id}/documentation.html"
    preview = open(html_path).read()

    return templates.TemplateResponse("result.html", {
        "request": request,
        "job_id": job_id,
        "preview_html": preview
    })


@app.get("/download/{job_id}/{filename}")
def download(job_id: str, filename: str):
    path = f"{OUTPUT_DIR}/{job_id}/{filename}"
    return FileResponse(path, filename=filename)
