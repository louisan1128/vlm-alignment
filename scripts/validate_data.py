#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED = (
    "01_G1_VIDEO.mp4",
    "01_G1_SIDE_VIDEO.mp4",
    "02_SOURCE_BVH.bvh",
    "03_SEG_DESCRIPTION.txt",
    "04_ACTION_PHASE.json",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate prepared G1/BVH pair data")
    parser.add_argument(
        "pairs",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "g1_pairs",
    )
    args = parser.parse_args()
    directories = sorted(path for path in args.pairs.iterdir() if path.is_dir())
    failures: list[str] = []
    for directory in directories:
        missing = [name for name in REQUIRED if not (directory / name).is_file()]
        if missing:
            failures.append(f"{directory.name}: {', '.join(missing)}")
            continue
        try:
            metadata = json.loads((directory / "04_ACTION_PHASE.json").read_text(encoding="utf-8"))
            metadata["action_window_from_source_bvh"]["start_phase"]
            metadata["action_window_from_source_bvh"]["end_phase"]
            metadata["same_normalized_window_on_g1"]["start_frame"]
            metadata["same_normalized_window_on_g1"]["end_frame"]
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            failures.append(f"{directory.name}: invalid action metadata ({error})")
    symlinks = list(args.pairs.rglob("*"))
    symlinks = [path for path in symlinks if path.is_symlink()]
    print(f"pairs={len(directories)}")
    print(f"incomplete_pairs={len(failures)}")
    print(f"symlinks={len(symlinks)}")
    if failures:
        print("\n".join(failures))
    if symlinks:
        print("Unexpected symlinks:")
        print("\n".join(str(path) for path in symlinks))
    if failures or symlinks:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
