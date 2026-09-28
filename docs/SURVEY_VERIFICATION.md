# Survey foundation verification — 2026-09-28

Revision scope: municipal data import and navigable `PadovaCentroSurvey` scene on `scandolo/unity-foundation`.

| Check | Result |
| --- | --- |
| Python geographic tests | 4 passed: metric projection, concavity/winding, courtyard holes, source/elevation integrity |
| Unity EditMode tests | 4 passed, 0 failed |
| macOS Development build | Succeeded, 0 warnings, 0 errors |
| Runtime scene | PadovaCentroSurvey |
| Input and state scenarios | 5 passed: movement, reset, plan toggle, pointer selection, Erbe viewpoint |
| Render inspection | Overview, plan, and Erbe screenshots captured and inspected |
| Player lifecycle | Runtime Pipeline reached; Player quit after verification |

The click test uses an interior point of the actual source polygon. A bounding-box centre fell in a real courtyard and correctly failed to select the building. This is now covered by the test scenario.

## Short-run measurements

Apple M4, 16 GB RAM; Development Player, 1600 × 1000 capture, 60 FPS cap/vsync. Four 120-frame counter windows sampled during roughly 22 seconds of runtime, including the input checks:

- FPS: 59.98–60.02.
- Mean frame time: 16.661–16.671 ms.
- GPU frame time: 3.19–3.43 ms.
- Unity allocated memory: approximately 107.6 MB; reserved: 257.1 MB. These are Unity allocator counters, not total process/GPU resident memory.

This scene uses per-feature renderers for source inspection and currently has high draw-call counts. Batch/stream geometry before growing the district. No 20-minute route, thermal measurements, final art or gameplay workload was tested. These measurements do not establish the 1080p/60 sustained game target.

## Local evidence and reproduction

- `.context/padova-player-verification.json`
- `.context/padova-editmode-tests.json`
- `.context/padova-build-summary.json`
- `.context/padova-survey-overview.png`
- `.context/padova-survey-plan.png`
- `.context/padova-survey-erbe.png`
- `.context/padova-player-unity.log`

Run `python3 Tools/verify_survey.py --build` to reproduce the native smoke run. Source/accuracy limits and remaining architectural work are in [REAL_WORLD_DATA.md](REAL_WORLD_DATA.md).
