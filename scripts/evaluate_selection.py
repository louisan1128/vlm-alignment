#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from vlm_alignment_v2.evaluator import evaluate_pair
from vlm_alignment_v2.models import PairPaths
from vlm_alignment_v2.renderer import render_source_bvh


def main() -> None:
    parser = argparse.ArgumentParser(description="Render and evaluate a saved motion selection")
    parser.add_argument("selection", type=Path)
    parser.add_argument("--pairs", type=Path, default=Path("data/g1_pairs"))
    parser.add_argument("--output", type=Path, default=Path("outputs/literal_only_20/new"))
    parser.add_argument("--render-workers", type=int, default=3)
    parser.add_argument("--samples", type=int, default=12)
    parser.add_argument("--sample-only", action="store_true")
    args = parser.parse_args()

    motions = json.loads(args.selection.read_text(encoding="utf-8"))["motions"]
    pairs = {name: PairPaths.from_directory(args.pairs / name) for name in motions}

    def render(name: str) -> tuple[str, Path]:
        video = render_source_bvh(pairs[name].source_bvh, args.output / name / "source_soma")
        return name, video

    with ThreadPoolExecutor(max_workers=args.render_workers) as executor:
        futures = {executor.submit(render, name): name for name in motions}
        for index, future in enumerate(as_completed(futures), start=1):
            name, video = future.result()
            print(f"[render {index}/{len(motions)}] {name}: {video}", flush=True)

    for index, name in enumerate(motions, start=1):
        output = args.output / name
        expected = output / ("PREPARED.json" if args.sample_only else "RESULT.json")
        if expected.is_file():
            print(f"[evaluate {index}/{len(motions)}] skip {name}", flush=True)
            continue
        print(f"[evaluate {index}/{len(motions)}] {name}", flush=True)
        result = evaluate_pair(
            pairs[name].root,
            output,
            samples=args.samples,
            sample_only=args.sample_only,
        )
        if not args.sample_only:
            print(f"  cosine={result['cosine_similarity']:.4f}", flush=True)


if __name__ == "__main__":
    main()
