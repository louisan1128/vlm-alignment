from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PairPaths:
    root: Path
    name: str
    g1_front: Path
    g1_side: Path
    source_bvh: Path
    seg_description: Path
    action_phase: Path

    @classmethod
    def from_directory(cls, directory: str | Path) -> "PairPaths":
        root = Path(directory).expanduser().resolve()
        files = {
            "g1_front": root / "01_G1_VIDEO.mp4",
            "g1_side": root / "01_G1_SIDE_VIDEO.mp4",
            "source_bvh": root / "02_SOURCE_BVH.bvh",
            "seg_description": root / "03_SEG_DESCRIPTION.txt",
            "action_phase": root / "04_ACTION_PHASE.json",
        }
        missing = [path.name for path in files.values() if not path.is_file()]
        if missing:
            raise FileNotFoundError(f"Incomplete pair {root}: missing {', '.join(missing)}")
        return cls(root=root, name=root.name, **files)


@dataclass(frozen=True)
class SampledFrame:
    order: int
    frame_index: int
    window_phase: float
    path: Path
