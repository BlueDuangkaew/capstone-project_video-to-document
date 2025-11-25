# Architecture & Processing Pipeline

This document describes the architecture of the Video → Polished Documentation platform and how upstream components work together to transform a short instructional video into a step-by-step HTML document powered by high-quality GIFs.

## Summary

Goal: Accept an instructional video (≤ 15 minutes) and produce a compressed, step-by-step HTML document where each step includes a short (2–4s) GIF demonstrating the action.

Key constraints:
- Max upload duration: 15 minutes (900 seconds).
- Accepted formats: MP4, MOV, WebM.
- Output: responsive HTML document embedding gifs / optional PDF export later.

## Components

- Upload API
  - Accepts video files and optional segment timestamps from the user.
  - Validates duration, format, and optionally triggers trimming suggestions if too long.

- Trimmer
  - Uses OpenCV and/or FFmpeg to trim original video into segments or to obey user-provided timestamps.
  - Enforces the 15-minute duration per video or per segment (based on design decision — currently global per upload).

- Event-based clip detector
  - Instead of picking single frames, this module finds short 2–4s clips where actions or transitions occur.
  - Techniques: OpenCV frame differencing, SSIM, histogram changes, motion vectors, cursor detection, UI transitions.

- Transcription & text pipeline
  - ASR (Whisper or similar) transcribes audio and segments into lines or steps.
  - Optional human correction or verification step.

- Clip–text alignment
  - Use CLIP-like models or embedding similarity to match each textual instruction line to a candidate 2–4s clip.
  - Weighting signals: visual similarity, OCR hints, motion dynamics, timestamp alignment, embedding scores.

- GIF generation
  - For each chosen clip, produce a small, smooth GIF with gifski.
  - Steps:
    1. Extract a short MP4 clip (2–4s).
    2. Convert frames to PNG or pass directly to gifski.
    3. Optimize gifski options for small sizes and smooth motion.
  - Aim for ~100–300 KB per GIF using gifski tuning.

- HTML Document Builder
  - Compose a clean responsive HTML document with an ordered sequence of steps. Each step contains a headline, gif, and supporting text.
  - Example structure:

```html
<h1>Instruction Manual</h1>

<div class="step">
  <h2>1. Right-click the folder</h2>
  <img src="gif_001.gif" alt="Right-click folder">
  <p>Then select "Properties".</p>
</div>
```

## Why GIFs (gifski)?

- gifski produces higher quality, smaller file sizes compared to GIF creation alternatives.
- Preserves smooth motion and is well suited to short instructional clips.
- Command-line friendly for pipeline automation.

## Deployment considerations

- Storage and caching of GIFs and HTML outputs.
- CDN delivery to improve download performance.
- Optionally: transcode to video preview formats and/or generate PDF versions of the document.

## Size, bandwidth and UX

- Recommend limiting steps per document (or downsampling frame rates) to keep outputs under a reasonable download size.
- Provide preview and download options in the web UI to inspect final output.

## Next steps

- Implement validation & trimming helpers.
- Add tests to enforce duration and format validation.
- Implement event-based clip detection & gifski generation modules.
