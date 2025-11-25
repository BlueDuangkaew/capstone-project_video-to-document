from __future__ import annotations

"""src.main
---------------
Entry point for the Video -> Polished Documentation pipeline.

This module provides a small CLI that supports two modes:
 - "serve" — run the FastAPI web app (uvicorn)
 - "run" — invoke the pipeline directly from the command-line

Example:
    python -m src.main run --input path/to/video.mp4 --outdir ./output

The code is intentionally defensive so importing this module in tests
does not start the web server nor require the full pipeline to be present.
"""

import argparse
import logging
from pathlib import Path
from typing import Optional

import uvicorn

# Try to import project logger helper (will exist once utils is created).
# If not present yet, fall back to a simple local helper so main remains
# importable for tests.
try:
    from src.utils.logger import get_logger  # type: ignore
except Exception:  # pragma: no cover - defensive
    def get_logger(name: str = "capstone") -> logging.Logger:
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger


DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """
    Command-line parsing with two modes:

    - serve: start the web UI (uvicorn) to accept uploads
    - run: run the pipeline directly from the CLI (keeps previous behavior)

    If no subcommand is provided we default to `serve` to make running the
    web front-end easier (e.g. `python -m src.main`).
    """
    p = argparse.ArgumentParser(
        prog="capstone",
        description="Run the project's web frontend (FastAPI/uvicorn).",
    )

    # Simple, focused CLI — web is the single supported entrypoint. Keep a
    # debug flag for verbose logging during development and host/port options
    # to override defaults.
    p.add_argument("--host", default=DEFAULT_HOST, help="Host to bind the server to")
    p.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to listen on")
    p.add_argument("--reload", action="store_true", help="Enable uvicorn --reload for development")
    p.add_argument("--debug", action="store_true", help="Enable debug logging")

    return p.parse_args(argv)


def ensure_outdir(path: str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p.resolve()


def _start_server(app_module: str, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, reload: bool = False) -> None:
    """Start a uvicorn server for the given app module path.

    This helper is intentionally small so tests can monkeypatch uvicorn.run
    on the module without launching a server.
    """
    uvicorn.run(app_module, host=host, port=port, reload=reload)


# The project now uses the web app as the canonical way to run the pipeline.
# We intentionally removed the 'run' CLI mode so `main()` focuses on starting
# the webserver. Pipeline execution is expected to go through the web UI.



def main(argv: Optional[list[str]] = None) -> int:
    """
    Main entry point.

    Returns:
        int: exit code (0 success, non-zero fail)
    """
    args = parse_args(argv)
    logger = get_logger("capstone.main")
    if getattr(args, "debug", False):
        logger.setLevel(logging.DEBUG)

    # For this project we exclusively use the web app as the main entrypoint.
    host = getattr(args, "host", DEFAULT_HOST)
    port = getattr(args, "port", DEFAULT_PORT)
    reload_flag = getattr(args, "reload", False)

    logger.info("Starting web server on %s:%s (reload=%s)", host, port, reload_flag)
    _start_server("src.web.app:app", host=host, port=port, reload=reload_flag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
