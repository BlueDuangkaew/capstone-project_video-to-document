"""Utility to clean stale uploaded data and generated output files.

This module removes files older than TTL seconds from a configurable set
of directories. It uses pathlib for clarity and includes logging so the
operation can be safely run from a daily cron job or as a simple script.
"""

from pathlib import Path
import logging

logger = logging.getLogger(__name__)
import time
import shutil
import logging
from typing import Iterable

logger = logging.getLogger(__name__)

# Default time-to-live: 24 hours
DEFAULT_TTL_SECONDS = 24 * 3600


def cleanup(paths: Iterable[Path] | None = None, ttl: int = DEFAULT_TTL_SECONDS) -> int:
    """Remove files older than `ttl` seconds under each path.

    Args:
        paths: Iterable of Path objects or None to use the default set.
        ttl: Time-to-live in seconds; entries older than this are removed.

    Returns:
        Number of items removed.
    """
    if paths is None:
        # Resolve directories relative to the project root for predictable
        # behaviour regardless of working directory. `src/web` is two levels
        # deep from the repository root.
        project_root = Path(__file__).resolve().parents[2]
        paths = [project_root / "uploads", project_root / "output", Path("/tmp/jobs")]

    now = time.time()
    removed = 0

    for base in paths:
        if not base.exists():
            logger.debug("Skipping missing path: %s", base)
            continue

        for child in base.iterdir():
            try:
                mtime = child.stat().st_mtime
                if now - mtime > ttl:
                    if child.is_dir():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
                    removed += 1
                    logger.info("Removed stale item: %s", child)
            except Exception:
                logger.exception("Failed to remove: %s", child)

    return removed


if __name__ == "__main__":  # pragma: no cover - convenience script
    logging.basicConfig(level=logging.INFO)
    count = cleanup()
    print(f"Removed {count} stale items")
