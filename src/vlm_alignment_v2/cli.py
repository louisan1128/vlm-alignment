from __future__ import annotations

import argparse
import json
from pathlib import Path

from .evaluator import DEFAULT_PROMPT, evaluate_pair
from .models import PairPaths
from .renderer import render_source_bvh


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PAIRS = PROJECT_ROOT / "data" / "g1_pairs"
DEFAULT_OUTPUTS = PROJECT_ROOT / "outputs"


def shared_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--samples", type=int, default=12)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--vision-model", default="gpt-5.6-sol")
    parser.add_argument("--embedding-model", default="text-embedding-3-large")
    parser.add_argument("--image-detail", choices=("low", "high", "auto"), default="high")
    parser.add_argument("--sample-only", action="store_true", help="Prepare inputs without API calls")
    parser.add_argument("--force-render", action="store_true")


def write_batch_summary(output: Path, rows: list[dict]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "SUMMARY.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Batch Summary",
        "",
        "| Motion | Status | Cosine | Error |",
        "|---|---|---:|---|",
    ]
    for row in rows:
        score = row.get("cosine_similarity")
        score_text = f"{score:.4f}" if score is not None else "-"
        error = str(row.get("error", "")).replace("|", "\\|")
        lines.append(f"| {row['motion']} | {row['status']} | {score_text} | {error} |")
    (output / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate source-BVH to G1 motion alignment")
    subparsers = parser.add_subparsers(dest="command", required=True)

    listing = subparsers.add_parser("list", help="List available pair directories")
    listing.add_argument("--pairs", type=Path, default=DEFAULT_PAIRS)
    listing.add_argument("--pattern", default="*")

    render = subparsers.add_parser("render", help="Render one BVH as a SOMA front+side video")
    render.add_argument("bvh", type=Path)
    render.add_argument("output", type=Path)
    render.add_argument("--force", action="store_true")

    evaluate = subparsers.add_parser("evaluate", help="Evaluate one pair")
    evaluate.add_argument("pair", type=Path)
    evaluate.add_argument("--output", type=Path)
    shared_options(evaluate)

    batch = subparsers.add_parser("batch", help="Evaluate multiple pairs with resume support")
    batch.add_argument("--pairs", type=Path, default=DEFAULT_PAIRS)
    batch.add_argument("--output", type=Path, default=DEFAULT_OUTPUTS / "batch")
    batch.add_argument("--pattern", default="*")
    batch.add_argument("--limit", type=int)
    batch.add_argument("--force", action="store_true", help="Re-evaluate completed results")
    batch.add_argument("--stop-on-error", action="store_true")
    shared_options(batch)
    return parser


def run_evaluate(args: argparse.Namespace, pair: Path, output: Path) -> dict:
    return evaluate_pair(
        pair,
        output,
        samples=args.samples,
        prompt_path=args.prompt,
        vision_model=args.vision_model,
        embedding_model=args.embedding_model,
        image_detail=args.image_detail,
        sample_only=args.sample_only,
        force_render=args.force_render,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "list":
        for path in sorted(item for item in args.pairs.glob(args.pattern) if item.is_dir()):
            print(path.name)
        return
    if args.command == "render":
        print(render_source_bvh(args.bvh.resolve(), args.output.resolve(), force=args.force))
        return
    if args.command == "evaluate":
        pair = PairPaths.from_directory(args.pair)
        output = args.output or DEFAULT_OUTPUTS / pair.name
        result = run_evaluate(args, pair.root, output)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    pairs = sorted(item for item in args.pairs.glob(args.pattern) if item.is_dir())
    if args.limit is not None:
        pairs = pairs[: args.limit]
    summary = []
    for index, pair_path in enumerate(pairs, start=1):
        output = args.output / pair_path.name
        expected = output / ("PREPARED.json" if args.sample_only else "RESULT.json")
        try:
            if expected.is_file() and not args.force:
                print(f"[{index}/{len(pairs)}] skip {pair_path.name}")
                result = json.loads(expected.read_text(encoding="utf-8"))
            else:
                print(f"[{index}/{len(pairs)}] run {pair_path.name}", flush=True)
                result = run_evaluate(args, pair_path, output)
            summary.append(
                {
                    "motion": pair_path.name,
                    "cosine_similarity": result.get("cosine_similarity"),
                    "status": "prepared" if args.sample_only else "evaluated",
                }
            )
        except Exception as error:
            summary.append({"motion": pair_path.name, "status": "failed", "error": str(error)})
            write_batch_summary(args.output, summary)
            if args.stop_on_error:
                raise
            print(f"[{index}/{len(pairs)}] failed {pair_path.name}: {error}", flush=True)
            continue
        write_batch_summary(args.output, summary)


if __name__ == "__main__":
    main()
