#!/usr/bin/env python3
"""Prepare a five-way source/robot text-alignment evaluation without API calls.

The prepared inputs follow the literal20 protocol: twelve uniform samples inside
the source-derived action window, each as a normalized front|side composite.
Robot comparison renders contain labels and a source panel; this script crops
only the robot panel and moves its header out of view before saving VLM inputs.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from vlm_alignment_v2.framing import (
    G1_BACKGROUND,
    TARGET_BODY_HEIGHT,
    TARGET_FOOT_Y,
    make_contact_sheet,
    read_frame,
    save_composite,
    uniform_indices,
)
from vlm_alignment_v2.models import PairPaths, SampledFrame


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = PROJECT_ROOT / "data" / "cross_embodiment_10"
DEFAULT_PAIRS = PROJECT_ROOT / "data" / "g1_pairs"
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "cross_embodiment_literal_10_v1"
DEFAULT_PROMPT = PROJECT_ROOT / "prompts" / "motion_alignment_cross_embodiment_literal_v1.txt"


@dataclass(frozen=True)
class Motion:
    name: str
    pair_directory: str
    action_window: dict[str, object] | None = None


MOTIONS = (
    Motion("BELLY_RUB-3", "0062_BELLY_RUB-3"),
    Motion("EYES_RING-2", "0094_EYES_RING-2"),
    Motion("FINGERS_AIR_QUOTES-1", "0104_FINGERS_AIR_QUOTES-1"),
    Motion("FINGERS_BECKON-1", "0107_FINGERS_BECKON-1"),
    Motion("FIST_CLASP-2", "0148_FIST_CLASP-2"),
    Motion("FIST_KNOCK-1", "0151_FIST_KNOCK-1"),
    Motion("HANDS_STEERING-1", "0316_HANDS_STEERING-1"),
    Motion("HAND_TOAST-1", "0388_HAND_TOAST-1"),
    Motion("HEAD_SCRATCH-1", "0417_HEAD_SCRATCH-1"),
    Motion("NOSE_TOUCH-1", "0444_NOSE_TOUCH-1"),
)

METHODS = (
    ("ours_g1", "ours_vid", "g1_revo2", "Ours G1"),
    ("ours_alex", "ours_vid", "allex", "Ours Alex"),
    ("baseline_g1", "baseline2_vid", "g1_revo2", "Baseline G1"),
    ("baseline_alex", "baseline2_vid", "allex", "Baseline Alex"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_DATA / "manifest.json",
        help="Curated input manifest. Omit the file to use the legacy raw-data layout.",
    )
    parser.add_argument("--pairs", type=Path, default=DEFAULT_PAIRS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--samples", type=int, default=12)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def load_motions(manifest: Path) -> tuple[Motion, ...]:
    if not manifest.is_file():
        return MOTIONS
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    return tuple(
        Motion(
            name=item["motion"],
            pair_directory=item["pair_directory"],
            action_window=item["action_window"],
        )
        for item in payload["motions"]
    )


def resolve_robot_directory(root: Path, motion: str, robot: str) -> Path:
    matches = []
    for path in root.rglob(motion):
        if "__MACOSX" in path.parts or not path.is_dir() or path.parent.name != robot:
            continue
        if (path / "front.mp4").is_file() and (path / "side.mp4").is_file():
            matches.append(path)
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one {robot} render for {motion} under {root}, found {matches}")
    return matches[0]


def resolve_input_directory(
    root: Path,
    motion: str,
    key: str,
    collection: str,
    robot: str,
) -> Path:
    """Resolve either the compact Git layout or the original raw render tree."""
    curated = root / motion / key
    if (curated / "front.mp4").is_file() and (curated / "side.mp4").is_file():
        return curated
    return resolve_robot_directory(root / collection, motion, robot)


def robot_profile(robot: str) -> tuple[float, float, float]:
    """Fixed renderer calibration, determined from neutral G1/Alex comparison frames."""
    if robot == "g1_revo2":
        # A conservative fit leaves room for hands and wrist markers on motions
        # that raise the arms above the neutral head height.
        return 448.0 / 275.0, 240.0, 555.0
    if robot == "allex":
        return TARGET_BODY_HEIGHT / 340.0, 240.0, 600.0
    raise ValueError(f"No comparison-render calibration for {robot}")


def normalize_comparison_panel(frame: np.ndarray, profile: str) -> np.ndarray:
    """Extract a source or robot panel and place it at a fixed body-relative scale.

    Comparison overlays are deliberately removed: they contain motion and method
    names that would otherwise leak into the visual-language input.
    """
    height, width = frame.shape[:2]
    if (width, height) != (960, 604):
        raise ValueError(f"Expected 960x604 comparison render, got {width}x{height}")
    if profile == "soma":
        panel = frame[:, : width // 2].copy()
        background = tuple(int(value) for value in panel[200, 12])
        panel[:130] = background
        scale, center_x, foot_y = TARGET_BODY_HEIGHT / 436.0, 240.0, 576.0
    else:
        panel = frame[:, width // 2 :].copy()
        background = G1_BACKGROUND
        # The comparison renderer keeps its title, method, and left/right guide
        # above the robot head. Removing it prevents label leakage into VLM input.
        # HUD text ends around row 215. Stop well above the raised-hand region
        # (which begins around row 240 for the most vertical G1 gestures).
        panel[:228] = background
        scale, center_x, foot_y = robot_profile(profile)
    matrix = np.float32(
        [[scale, 0, 320.0 - scale * center_x], [0, scale, TARGET_FOOT_Y - scale * foot_y]]
    )
    return cv2.warpAffine(
        panel,
        matrix,
        (640, 640),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=background,
    )


def sample_comparison_embodiment(
    front_video: Path,
    side_video: Path,
    *,
    profile: str,
    start_phase: float,
    end_phase: float,
    count: int,
    output: Path,
) -> tuple[list[SampledFrame], dict[str, object]]:
    front = cv2.VideoCapture(str(front_video))
    side = cv2.VideoCapture(str(side_video))
    if not front.isOpened() or not side.isOpened():
        raise RuntimeError(f"Could not open synchronized robot views: {front_video}, {side_video}")
    try:
        usable = min(
            int(front.get(cv2.CAP_PROP_FRAME_COUNT)), int(side.get(cv2.CAP_PROP_FRAME_COUNT))
        )
        fps = float(front.get(cv2.CAP_PROP_FPS))
        start = int(round(start_phase * (usable - 1)))
        end = int(round(end_phase * (usable - 1)))
        start, end = max(0, start), min(usable - 1, end)
        indices = uniform_indices(start, end, count)
        frames: list[SampledFrame] = []
        for order, index in enumerate(indices, start=1):
            front_panel = normalize_comparison_panel(read_frame(front, int(index)), profile)
            side_panel = normalize_comparison_panel(read_frame(side, int(index)), profile)
            path = output / f"frame_{order:02d}_idx_{index:05d}.jpg"
            save_composite(front_panel, side_panel, path)
            frames.append(
                SampledFrame(
                    order, int(index), (int(index) - start) / max(1, end - start), path
                )
            )
    finally:
        front.release()
        side.release()
    make_contact_sheet(frames, output / "contact_sheet.jpg")
    return frames, {
        "front_video": str(front_video),
        "side_video": str(side_video),
        "frame_count": usable,
        "fps": fps,
        "projected_window": {"start_frame": start, "end_frame": end},
        "normalization": {
            "source_panel": "left SOMA half" if profile == "soma" else "right robot half",
            "output": "640x640 front and 640x640 side, concatenated to 1280x640",
            "method_and_motion_text_removed": True,
            "fixed_renderer_profile": profile,
        },
        "sampled_frames": [
            {"order": item.order, "frame_index": item.frame_index, "action_window_phase": item.window_phase}
            for item in frames
        ],
    }


def write_action_window_video(
    front_video: Path,
    side_video: Path,
    *,
    profile: str,
    start_phase: float,
    end_phase: float,
    output: Path,
) -> dict[str, object]:
    """Save every normalized frame in the action window for visual inspection."""
    front = cv2.VideoCapture(str(front_video))
    side = cv2.VideoCapture(str(side_video))
    if not front.isOpened() or not side.isOpened():
        raise RuntimeError(f"Could not open synchronized robot views: {front_video}, {side_video}")
    try:
        usable = min(
            int(front.get(cv2.CAP_PROP_FRAME_COUNT)), int(side.get(cv2.CAP_PROP_FRAME_COUNT))
        )
        fps = float(front.get(cv2.CAP_PROP_FPS))
        start = max(0, int(round(start_phase * (usable - 1))))
        end = min(usable - 1, int(round(end_phase * (usable - 1))))
        if output.is_file():
            return {
                "path": str(output),
                "frame_count": end - start + 1,
                "fps": fps,
                "projected_window": {"start_frame": start, "end_frame": end},
                "resolution": [1280, 640],
            }
        output.parent.mkdir(parents=True, exist_ok=True)
        intermediate = output.with_suffix(".intermediate.mp4")
        intermediate.unlink(missing_ok=True)
        writer = cv2.VideoWriter(
            str(intermediate), cv2.VideoWriter_fourcc(*"mp4v"), fps, (1280, 640)
        )
        if not writer.isOpened():
            raise RuntimeError(f"Could not create action-window video: {output}")
        try:
            for index in range(start, end + 1):
                front_panel = normalize_comparison_panel(read_frame(front, index), profile)
                side_panel = normalize_comparison_panel(read_frame(side, index), profile)
                writer.write(np.concatenate((front_panel, side_panel), axis=1))
        finally:
            writer.release()
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error", "-i", str(intermediate),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output),
            ],
            check=True,
        )
        intermediate.unlink()
    finally:
        front.release()
        side.release()
    return {
        "path": str(output),
        "frame_count": end - start + 1,
        "fps": fps,
        "projected_window": {"start_frame": start, "end_frame": end},
        "resolution": [1280, 640],
    }


def relative(path: Path, from_path: Path) -> str:
    return str(path.relative_to(from_path.parent))


def write_report(output: Path, manifest: dict[str, object]) -> None:
    lines = [
        "# Cross-Embodiment Literal Alignment: Prepared Inputs",
        "",
        "## Status",
        "",
        "- **Prepared only. No OpenAI API call has been made.**",
        "- Each motion has five independently captioned inputs: Source SOMA, Ours G1, Ours Alex, Baseline G1, and Baseline Alex.",
        "- Final scoring will compare the Source SOMA caption with each of the four robot captions using `text-embedding-3-large` cosine similarity.",
        "",
        "## Frozen Protocol",
        "",
        "- Views: synchronized front + side, packed into one `1280x640` composite per temporal sample.",
        "- Temporal window: source-BVH action window (`start_phase` to `end_phase`) projected onto every rendition's normalized timeline.",
        "- Sampling: 12 uniform phases inside that window, identical to the literal20 protocol.",
        "- Source: left SOMA panel from the provided synchronized comparison renders; no BVH re-rendering is performed.",
        "- Robot renders: right robot panel only; comparison labels, method names, and motion names are outside the normalized canvas.",
        "- Prompt: one shared literal physical-motion prompt. No SeG label or SeG description is provided to the VLM.",
        "- Planned model: `gpt-5.6-sol`, `high` image detail; embeddings: `text-embedding-3-large`.",
        "",
        "## Planned API Work",
        "",
        "- Vision calls: **50** (`10 motions x 5 embodiments`).",
        "- Embedding comparisons: **40** (`10 motions x 4 robot targets vs source`).",
        "- The report will be updated with five captions and four cosine scores per motion after explicit approval.",
        "",
        "## Shared Prompt",
        "",
        "```text",
        (output / "PROMPT.txt").read_text(encoding="utf-8").strip(),
        "```",
        "",
        "## Inputs By Motion",
        "",
    ]
    motions = manifest["motions"]
    for row in motions:
        lines.extend(
            [
                f"### {row['motion']}",
                "",
                f"- Source action window: phase **{row['source_action_window']['start_phase']:.3f} to {row['source_action_window']['end_phase']:.3f}**",
                f"- Source BVH: `{row['pair_directory']}`",
                "",
            ]
        )
        for key, title in (("source_soma", "Source SOMA"), ("ours_g1", "Ours G1"), ("ours_alex", "Ours Alex"), ("baseline_g1", "Baseline G1"), ("baseline_alex", "Baseline Alex")):
            sheet = output / row["inputs"][key]["contact_sheet"]
            video = output / row["inputs"][key]["action_window_video"]
            lines.extend(
                [
                    "<details>",
                    f"<summary><strong>{title}</strong> - 12 uniform action-window samples</summary>",
                    "",
                    f"![{title} contact sheet]({relative(sheet, output / 'PREPARATION_REPORT.md')})",
                    "",
                    "</details>",
                    "",
                    "<details>",
                    f"<summary><strong>{title} action-window video</strong></summary>",
                    "",
                    f'<video controls preload="metadata" width="960" src="{relative(video, output / "PREPARATION_REPORT.md")}"></video>',
                    "",
                    f"[Open video]({relative(video, output / 'PREPARATION_REPORT.md')})",
                    "",
                    "</details>",
                    "",
                ]
            )
    (output / "PREPARATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    output = args.output.resolve()
    if output.exists() and args.force:
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.prompt, output / "PROMPT.txt")

    manifest: dict[str, object] = {
        "schema_version": "1.0",
        "status": "prepared_no_api_calls",
        "protocol": {
            "views": ["front", "side"],
            "samples": args.samples,
            "action_window": "source-BVH normalized phase projected into each rendition timeline",
            "source_renderer": "provided SOMA source panel from the synchronized comparison render; no new rendering",
            "robot_input": "right robot panel cropped from front/side comparison renders and normalized to a fixed renderer profile",
            "prompt": "PROMPT.txt",
            "vision_model_for_later": "gpt-5.6-sol",
            "image_detail_for_later": "high",
            "embedding_model_for_later": "text-embedding-3-large",
        },
        "motions": [],
    }
    selections = load_motions(args.manifest)
    for selection in selections:
        pair_root = args.pairs / selection.pair_directory
        if selection.action_window is None:
            pair = PairPaths.from_directory(pair_root)
            metadata = json.loads(pair.action_phase.read_text(encoding="utf-8"))
            window = metadata["action_window_from_source_bvh"]
        else:
            window = selection.action_window
        motion_output = output / selection.name
        source_directory = resolve_input_directory(
            args.data, selection.name, "ours_g1", "ours_vid", "g1_revo2"
        )
        _source_frames, source_record = sample_comparison_embodiment(
            source_directory / "front.mp4",
            source_directory / "side.mp4",
            profile="soma",
            start_phase=float(window["start_phase"]),
            end_phase=float(window["end_phase"]),
            count=args.samples,
            output=motion_output / "inputs" / "source_soma",
        )
        source_record["contact_sheet"] = str((motion_output / "inputs" / "source_soma" / "contact_sheet.jpg").relative_to(output))
        source_record["source_comparison_render"] = str(source_directory)
        source_record["action_window_video"] = str(
            (motion_output / "inputs" / "source_soma" / "action_window.mp4").relative_to(output)
        )
        write_action_window_video(
            source_directory / "front.mp4", source_directory / "side.mp4",
            profile="soma", start_phase=float(window["start_phase"]), end_phase=float(window["end_phase"]),
            output=motion_output / "inputs" / "source_soma" / "action_window.mp4",
        )
        inputs: dict[str, dict[str, object]] = {"source_soma": source_record}
        for key, collection, robot, _title in METHODS:
            directory = resolve_input_directory(
                args.data, selection.name, key, collection, robot
            )
            _frames, record = sample_comparison_embodiment(
                directory / "front.mp4",
                directory / "side.mp4",
                profile=robot,
                start_phase=float(window["start_phase"]),
                end_phase=float(window["end_phase"]),
                count=args.samples,
                output=motion_output / "inputs" / key,
            )
            record["contact_sheet"] = str((motion_output / "inputs" / key / "contact_sheet.jpg").relative_to(output))
            record["action_window_video"] = str(
                (motion_output / "inputs" / key / "action_window.mp4").relative_to(output)
            )
            write_action_window_video(
                directory / "front.mp4", directory / "side.mp4",
                profile=robot, start_phase=float(window["start_phase"]), end_phase=float(window["end_phase"]),
                output=motion_output / "inputs" / key / "action_window.mp4",
            )
            inputs[key] = record
        motion_record = {
            "motion": selection.name,
            "pair_directory": str(pair_root),
            "source_action_window": window,
            "inputs": inputs,
        }
        (motion_output / "SAMPLING.json").write_text(
            json.dumps(motion_record, indent=2) + "\n", encoding="utf-8"
        )
        manifest["motions"].append(motion_record)
        print(f"Prepared {selection.name}")
    (output / "PREPARATION_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    write_report(output, manifest)
    print(f"Prepared {len(selections)} motions at {output}")


if __name__ == "__main__":
    main()
