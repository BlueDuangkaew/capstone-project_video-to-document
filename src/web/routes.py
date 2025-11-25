from typing import Dict

from fastapi import APIRouter

router = APIRouter()


@router.get("/", response_model=Dict[str, str])
def root() -> Dict[str, str]:
    """Lightweight root endpoint for programmatic health checks."""
    return {"message": "Welcome to the Video-to-Documentation Platform"}


@router.get("/health", response_model=Dict[str, str])
def health() -> Dict[str, str]:
    """Simple health endpoint.

    Useful for load balancers / uptime checks.
    """
    return {"status": "ok"}
