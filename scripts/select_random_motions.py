#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


DEFAULT_EXCLUDE = {
    "0001_ARMS_AKIMBO-1",
    "0060_BELLY_PREGNANT-1",
    "0097_EYE_TELESCOPE-3",
    "0104_FINGERS_AIR_QUOTES-1",
    "0107_FINGERS_BECKON-1",
    "0148_FIST_CLASP-2",
    "0151_FIST_KNOCK-1",
    "0316_HANDS_STEERING-1",
    "0388_HAND_TOAST-1",
    "0417_HEAD_SCRATCH-1",
    "0444_NOSE_TOUCH-1",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Select a reproducible random motion subset")
    parser.add_argument("--pairs", type=Path, default=Path("data/g1_pairs"))
    parser.add_argument("--count", type=int, default=9)
    parser.add_argument("--seed", type=int, default=20260908)
    parser.add_argument("--output", type=Path, default=Path("outputs/random_9_selection.json"))
    args = parser.parse_args()

    population = sorted(
        path.name
        for path in args.pairs.iterdir()
        if path.is_dir() and path.name not in DEFAULT_EXCLUDE
    )
    selected = sorted(random.Random(args.seed).sample(population, args.count))
    payload = {"seed": args.seed, "population_size": len(population), "motions": selected}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
