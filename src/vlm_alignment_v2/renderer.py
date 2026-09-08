from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RENDER_SCRIPT = PROJECT_ROOT / "scripts" / "render_bvh_to_soma.py"


def render_source_bvh(bvh: Path, output: Path, *, force: bool = False) -> Path:
    video = output / "soma_front_side.mp4"
    if video.is_file() and not force:
        return video
    output.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, str(RENDER_SCRIPT), str(bvh), str(output)],
        check=True,
    )
    if not video.is_file():
        raise RuntimeError(f"SOMA renderer did not create {video}")
    return video
