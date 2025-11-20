import os
from pathlib import Path

def ensure_dir(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)

def frame_save_path(base_dir: str, scene_idx: int) -> str:
    return os.path.join(base_dir, f"scene_{scene_idx:03d}.jpg")
