# Two-minute Atlas walkthrough

[Watch the narrated walkthrough](atlas-walkthrough.mp4).

This 1280×720 video pans across genuine application screenshots with synthesized narration. It is a **screenshot walkthrough, not a live interaction recording**. The screenshots predate the final KPI wrapping and forecast-band fixes. The narration describes the verified local application and distinguishes guided regression results from live-model evaluation.

Chapters: overview (0:00), investigation (0:30), analytical evidence (1:00), review brief (1:30). The full narration is available in `narration.json` for accessibility and reuse.

To regenerate on macOS: install the optional authoring dependency `imageio-ffmpeg`, then run `.venv/bin/python scripts/build_demo.py`. The script uses macOS `say` and writes temporary media into ignored `.runtime/demo`.
