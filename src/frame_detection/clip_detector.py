"""Simple event-based clip detector.

This helper chooses a short clip (2-4 seconds by default) for a given
timeline entry. It prefers using the transcript-provided start/end when
available and will attempt to refine the clip by looking for high-motion
areas near the provided interval when OpenCV is available.

The implementation is intentionally conservative and will fall back to
the provided timestamps if any step fails.
"""
from __future__ import annotations

import logging
from typing import List, Dict, Tuple
import math

logger = logging.getLogger(__name__)

try:
    import cv2
except Exception:  # pragma: no cover - cv2 may not be available in some envs
    cv2 = None

try:
    import pytesseract  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pytesseract = None


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _seconds_from_item(item: Dict) -> Tuple[float, float]:
    # Accept either numeric seconds or seconds-like values stored under
    # 'start_seconds'/'end_seconds' (cleaner) or raw numeric 'start'/'end'.
    s = item.get("start_seconds") if item.get("start_seconds") is not None else item.get("start")
    e = item.get("end_seconds") if item.get("end_seconds") is not None else item.get("end")
    try:
        return float(s or 0.0), float(e or s or 0.0)
    except Exception:
        return 0.0, 0.0


def _detect_text_in_frame(frame) -> bool:
    """Return True if OCR detects textual content in the frame.

    This is intentionally simple. If pytesseract is not available we raise
    a RuntimeError so callers can fall back. Tests may monkeypatch this
    function to simulate text detection.
    """
    if pytesseract is None:
        raise RuntimeError("pytesseract not available")

    # Use pytesseract to extract text and accept small strings
    try:
        text = pytesseract.image_to_string(frame or "")
        return bool(text and len(text.strip()) > 2)
    except Exception:
        return False


def _find_motion_peak(video_path: str, window_start: float, window_end: float, target: float, sample_fps: float = 2.0, ocr_weight: float = 0.0) -> Tuple[float, float]:
    """Scan a small window for motion and return the best start/end in seconds.

    This function samples frames at a low rate (sample_fps) and computes
    inter-frame differences. It then slides a window equal to `target`
    seconds across the sampled timestamps and picks the window with the
    highest aggregate motion.

    If OpenCV is not available or any error occurs, raise an Exception so
    callers can fall back to simpler logic.
    """
    if cv2 is None:
        raise RuntimeError("OpenCV (cv2) not available")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Unable to open video for motion analysis")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    # Sample every sample_step seconds
    sample_step = 1.0 / sample_fps
    timestamps = []
    diffs = []
    ocr_flags = []

    # Seek the start
    cap.set(cv2.CAP_PROP_POS_MSEC, window_start * 1000.0)
    prev_gray = None
    t = window_start
    while t <= window_end:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        timestamps.append(t)
        if prev_gray is not None:
            # Mean absolute difference is a cheap motion proxy
            motion = float(cv2.absdiff(gray, prev_gray).mean())
            diffs.append(motion)
        else:
            diffs.append(0.0)

        # Optionally detect text in the frame (OCR). We call the helper when
        # ocr_weight is non-zero; the helper will raise or return False if
        # OCR isn't available — tests can monkeypatch _detect_text_in_frame.
        if ocr_weight:
            try:
                ocr_present = _detect_text_in_frame(frame)
            except Exception:
                ocr_present = False
        else:
            ocr_present = False

        ocr_flags.append(bool(ocr_present))
        prev_gray = gray
        t += sample_step

    cap.release()

    if not timestamps:
        raise RuntimeError("No frames sampled for motion analysis")

    # Convert target length to number of samples to slide over
    window_samples = max(1, int(math.ceil(target * sample_fps)))

    # Sum diffs in a sliding window; boost windows with OCR flags according
    # to ocr_weight so frames containing OCR text are favored.
    best_idx = 0
    best_score = -1.0
    for i in range(0, len(diffs) - window_samples + 1):
        motion_sum = sum(diffs[i : i + window_samples])
        ocr_count = sum(1 for flag in ocr_flags[i : i + window_samples] if flag)
        score = motion_sum + (ocr_count * ocr_weight)
        if score > best_score:
            best_score = score
            best_idx = i

    start_time = timestamps[best_idx]
    # Ensure we don't exceed available timestamps
    end_idx = min(len(timestamps) - 1, best_idx + window_samples - 1)
    end_time = timestamps[end_idx]

    # Expand to desired target (in seconds) centering the window
    mid = (start_time + end_time) / 2.0
    out_start = max(0.0, mid - target / 2.0)
    out_end = out_start + target
    return out_start, out_end


def detect_action_clips(video_path: str, timeline: List[Dict], target: float = 3.0, min_len: float = 2.0, max_len: float = 4.0, ocr_weight: float = 3.0) -> List[Dict]:
    """Add optional ocr_weight param to allow callers to tune how strongly
    OCR presence influences clip scoring.

    Backwards compatible: if not provided, we use the default weight inside.
    """
    """For each timeline item return a clip dict with start/end seconds.

    - Uses segment start/end when available and surrounding padding to reach
      the target length.
    - Attempts to refine using motion analysis within a small padded window
      around the candidate clip; if that analysis fails, falls back to
      deterministic logic.
    """
    out = []
    for item in timeline:
        try:
            start, end = _seconds_from_item(item)

            # Default bounds
            length = max(0.0, end - start)
            target_length = _clamp(target, min_len, max_len)

            if length >= target_length:
                clip_start = start
                clip_end = start + target_length
            else:
                extra = (target_length - length) / 2.0
                clip_start = max(0.0, start - extra)
                clip_end = end + extra

            # Try to refine using motion analysis if possible
            # We only attempt analysis in a modest window around the candidate
            # clip to keep CPU cost bounded.
            padded_start = max(0.0, clip_start - 1.0)
            padded_end = clip_end + 1.0
            try:
                # Respect caller-configured ocr_weight so tests can force a strong
                # bias if necessary (e.g., monkeypatched OCR detection behavior).
                refined_start, refined_end = _find_motion_peak(video_path, padded_start, padded_end, target_length, ocr_weight=ocr_weight)
                clip_start, clip_end = refined_start, refined_end
            except Exception:
                # If motion analysis fails, keep our deterministic clip
                logger.debug("Motion peak detection failed for item, using fallback: %s", item)

            out.append({"start": float(clip_start), "end": float(clip_end)})

        except Exception as e:
            logger.warning("Failed to pick clip for timeline item %s: %s", item, e)
            # fallback: provide a small clip at 0s
            out.append({"start": 0.0, "end": _clamp(target, min_len, max_len)})

    return out
