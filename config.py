from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
    LLAMA_MODEL = os.getenv("LLAMA_MODEL")
    UPLOAD_PATH = os.getenv("UPLOAD_PATH", "data/input_videos")
    LOG_PATH = os.getenv("LOG_PATH", "output/logs")

config = Config()
