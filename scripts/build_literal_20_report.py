#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "results" / "literal_only_20"


def portable_row(group: str, result: dict) -> dict:
    return {
        "group": group,
        "motion": result["motion"],
        "source_soma_literal": result.get("source_soma_literal", result.get("soma_literal")),
        "g1_literal": result["g1_literal"],
        "cosine_similarity": result.get("cosine_similarity", result.get("literal_only_cosine")),
        "usage": result.get("usage", {}),
    }


def copy_artifacts(row: dict) -> None:
    name = row["motion"]
    destination = DESTINATION / "artifacts" / name
    destination.mkdir(parents=True, exist_ok=True)
    if row["group"] == "original_10":
        source = ROOT / "results" / "literal_only_10"
        files = {
            source / "contact_sheets" / name / "soma.jpg": destination / "soma_contact_sheet.jpg",
            source / "contact_sheets" / name / "g1.jpg": destination / "g1_contact_sheet.jpg",
            source / "source_soma_videos" / f"{name}.mp4": destination / "source_soma.mp4",
        }
    else:
        source = (
            ROOT / "outputs" / "smoke_akimbo"
            if row["group"] == "akimbo"
            else ROOT / "outputs" / "literal_only_20" / "new" / name
        )
        files = {
            source / "inputs" / "soma" / "contact_sheet.jpg": destination / "soma_contact_sheet.jpg",
            source / "inputs" / "g1" / "contact_sheet.jpg": destination / "g1_contact_sheet.jpg",
            source / "source_soma" / "soma_front_side.mp4": destination / "source_soma.mp4",
        }
    for source, target in files.items():
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copy2(source, target)


def main() -> None:
    original = json.loads(
        (ROOT / "results" / "literal_only_10" / "RESULTS.json").read_text(encoding="utf-8")
    )
    akimbo = json.loads((ROOT / "outputs" / "smoke_akimbo" / "RESULT.json").read_text(encoding="utf-8"))
    selection = json.loads(
        (ROOT / "outputs" / "literal_only_20" / "random_9_selection.json").read_text(encoding="utf-8")
    )
    random_results = [
        json.loads(
            (ROOT / "outputs" / "literal_only_20" / "new" / name / "RESULT.json").read_text(
                encoding="utf-8"
            )
        )
        for name in selection["motions"]
    ]
    rows = (
        [portable_row("original_10", result) for result in original]
        + [portable_row("akimbo", akimbo)]
        + [portable_row("random_9", result) for result in random_results]
    )
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for row in rows:
        copy_artifacts(row)

    scores = [float(row["cosine_similarity"]) for row in rows]
    original_scores = [float(row["cosine_similarity"]) for row in rows if row["group"] == "original_10"]
    new_scores = [float(row["cosine_similarity"]) for row in rows if row["group"] == "random_9"]
    payload = {
        "protocol": {
            "source": "SeG BVH rendered as corrected SOMA mesh",
            "target": "retargeted G1 front and side videos",
            "sampling": "12 uniform action-window phases",
            "prompt": "literal-only v1; no SeG label or description prior",
            "vision_model": "gpt-5.6-sol",
            "embedding_model": "text-embedding-3-large",
        },
        "selection": selection,
        "summary": {
            "count": len(rows),
            "mean": sum(scores) / len(scores),
            "minimum": min(scores),
            "maximum": max(scores),
            "original_10_mean": sum(original_scores) / len(original_scores),
            "random_9_mean": sum(new_scores) / len(new_scores),
            "akimbo": float(akimbo["cosine_similarity"]),
            "at_least_0_75": sum(score >= 0.75 for score in scores),
            "at_least_0_80": sum(score >= 0.80 for score in scores),
            "at_least_0_85": sum(score >= 0.85 for score in scores),
        },
        "results": rows,
    }
    (DESTINATION / "RESULTS.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    shutil.copy2(
        ROOT / "prompts" / "motion_alignment_literal_only_v1.txt",
        DESTINATION / "PROMPT.txt",
    )

    lines = [
        "# Literal-Only 20-Motion Evaluation",
        "",
        "## Evaluation protocol",
        "",
        "- Source: SeG BVH rendered as corrected SOMA mesh with anatomical finger mapping and no IK",
        "- Target: retargeted G1 front and side videos",
        "- Window: source-BVH action window mapped to both embodiments by normalized phase",
        "- Input: 12 uniformly sampled synchronized front+side composites",
        "- VLM: `gpt-5.6-sol`, high image detail, identical literal-only prompt",
        "- Similarity: `text-embedding-3-large` cosine between independent SOMA and G1 descriptions",
        "- No SeG motion name or description is given to the VLM",
        "",
        "## Summary",
        "",
        f"- Total mean: **{payload['summary']['mean']:.4f}** across 20 motions",
        f"- Original 10 mean: **{payload['summary']['original_10_mean']:.4f}**",
        f"- ARMS_AKIMBO-1: **{payload['summary']['akimbo']:.4f}**",
        f"- Random 9 mean: **{payload['summary']['random_9_mean']:.4f}**",
        f"- Range: **{payload['summary']['minimum']:.4f}–{payload['summary']['maximum']:.4f}**",
        f"- Scores ≥0.75: **{payload['summary']['at_least_0_75']}/20**; "
        f"≥0.80: **{payload['summary']['at_least_0_80']}/20**; "
        f"≥0.85: **{payload['summary']['at_least_0_85']}/20**",
        f"- Random selection seed: `{selection['seed']}` from {selection['population_size']} eligible motions",
        "",
        "| Group | Motion | Cosine |",
        "|---|---|---:|",
    ]
    labels = {"original_10": "Existing 10", "akimbo": "Akimbo", "random_9": "Random 9"}
    for row in rows:
        lines.append(f"| {labels[row['group']]} | {row['motion']} | {row['cosine_similarity']:.4f} |")
    lines.extend(
        [
            "",
            "## Result interpretation",
            "",
            "- The 20-motion mean is useful as a pilot alignment score under one frozen protocol.",
            "- High cosine generally reflects matching active limbs, direction, body region, and temporal order.",
            "- Cosine can remain high when a semantically important detail differs, such as forehead contact versus an overhead pose.",
            "- Lower scores can also come from harmless wording differences, so this metric should be paired with relation-level or kinematic checks in the paper.",
            "- Lowest scores were HEAD_SCRATCH-1 (0.6525), FIST_KNOCK-1 (0.6758), and ARMS_AKIMBO-1 (0.6966).",
            "",
            "### Important qualitative cases",
            "",
            "- `FOREFINGER_EMPTY-2` (0.9210): both observations agree on the left hand above the right hand and the same temporal order; this is a strong match.",
            "- `FOREHEAD_WIPE-2` (0.7701): SOMA shows the hand against the forehead and eyes, while G1 is described as near the head and oscillating; contact and motion type differ.",
            "- `FOREHEAD_SALUTE-3` (0.8247): SOMA is positioned near the forehead, but G1 reaches above the head. The high score is driven by the shared right-arm raise-and-hold pattern.",
            "- `HAND_PURSE-2` (0.7732): source targets the mouth while G1 targets the forehead, showing that cosine does not isolate the target body region strongly enough.",
            "- `ARMS_AKIMBO-1` (0.6966): the defining hands-on-hips and elbows-out relation matches visually, but extra head and recovery wording lowers the score.",
            "",
            "## Motion-by-motion inspection",
            "",
        ]
    )
    for row in rows:
        name = row["motion"]
        lines.extend(
            [
                f"### {name}",
                "",
                f"- **Group:** {labels[row['group']]}",
                f"- **Cosine:** {row['cosine_similarity']:.4f}",
                f"- **Source SOMA:** {row['source_soma_literal']}",
                f"- **G1:** {row['g1_literal']}",
                "- **Visuals:** "
                f"[SOMA sheet](artifacts/{name}/soma_contact_sheet.jpg) | "
                f"[G1 sheet](artifacts/{name}/g1_contact_sheet.jpg) | "
                f"[SOMA video](artifacts/{name}/source_soma.mp4)",
                "",
            ]
        )
    (DESTINATION / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(DESTINATION / "REPORT.md")


if __name__ == "__main__":
    main()
