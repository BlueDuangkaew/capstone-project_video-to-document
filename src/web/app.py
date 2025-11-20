from fastapi import FastAPI
from .routes import router

def create_app():
    app = FastAPI(title="Video-to-Documentation Platform")
    app.include_router(router)
    return app

app = create_app()
