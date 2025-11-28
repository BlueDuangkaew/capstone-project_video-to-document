# Blue Progress Report — 2025-11-07 to 2025-11-20

**Student Name:** Kadpon Duangkaew  
**Nickname:** Blue

## Date range
2025-11-07 — 2025-11-20 (bi-weekly)

## Activities & accomplishments
- Finalized CI and Docker improvements; stabilized a CI matrix that runs linting and mocked unit tests to avoid heavy model downloads in CI.
- Implemented packaging improvements and Dockerfile tweaks to ensure ffmpeg and gifski are installed in the container for smoke tests.
- Added more end-to-end smoke tests for the upload→pipeline→download workflow using small sample videos (marked opt-in for CI to conserve resources).
- Completed a first pass of performance optimization: added sampling and throttling heuristics to clip detection to improve runtime predictability.

## Problems / Issues encountered
- Docker images that include heavy binaries are large; suggested alternative staging where smoke tests run in a dedicated job rather than the main CI flow.
- Some platform differences (e.g., ffmpeg behavior) still cause occasional discrepancies in test durations; documented a tolerance strategy in tests.

---

Let me know if you'd like these smoke tests enabled in CI or run only manually during release builds.