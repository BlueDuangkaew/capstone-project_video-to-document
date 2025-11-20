import json
import os

def load_segments(json_path):
    """
    Loads segments from segments.json
    Format:
    [
      { "start": 0, "end": 60, "name": "vid1.mp4" }
    ]
    """
    with open(json_path, "r") as f:
        return json.load(f)
