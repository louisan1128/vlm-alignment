from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .framing import sample_g1, sample_soma
from .models import PairPaths
from .provider import OpenAIProvider
from .renderer import render_source_bvh


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROMPT = PROJECT_ROOT / "prompts" / "motion_alignment_literal_only_v1.txt"


def prepare_inputs(
    pair: PairPaths,
    output: Path,
    *,
    samples: int = 12,
    force_render: bool = False,
) -> dict[str, Any]:
    soma_video = render_source_bvh(pair.source_bvh, output / "source_soma", force=force_render)
    soma_frames = sample_soma(soma_video, pair, samples, output / "inputs" / "soma")
    g1_frames = sample_g1(pair, samples, output / "inputs" / "g1")
    return {"soma_video": soma_video, "soma_frames": soma_frames, "g1_frames": g1_frames}


def evaluate_pair(
    pair_directory: str | Path,
    output_directory: str | Path,
    *,
    samples: int = 12,
    prompt_path: str | Path = DEFAULT_PROMPT,
    vision_model: str = "gpt-5.6-sol",
    embedding_model: str = "text-embedding-3-large",
    image_detail: str = "high",
    sample_only: bool = False,
    force_render: bool = False,
) -> dict[str, Any]:
    pair = PairPaths.from_directory(pair_directory)
    output = Path(output_directory).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    prepared = prepare_inputs(pair, output, samples=samples, force_render=force_render)
    base: dict[str, Any] = {
        "schema_version": "2.0",
        "motion": pair.name,
        "pair_directory": str(pair.root),
        "protocol": {
            "source_representation": "SOMA mesh with direct local-rotation and anatomical finger transfer; no IK",
            "views": ["front", "side"],
            "sampling": "uniform within the source-derived action window",
            "samples": samples,
            "body_height_pixels": 512,
            "image_detail": image_detail,
            "prompt": Path(prompt_path).name,
            "vision_model": vision_model,
            "embedding_model": embedding_model,
        },
        "artifacts": {
            "source_soma_video": str(prepared["soma_video"]),
            "soma_contact_sheet": str(output / "inputs" / "soma" / "contact_sheet.jpg"),
            "g1_contact_sheet": str(output / "inputs" / "g1" / "contact_sheet.jpg"),
        },
    }
    if sample_only:
        (output / "PREPARED.json").write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
        return base

    prompt = Path(prompt_path).read_text(encoding="utf-8")
    provider = OpenAIProvider(
        vision_model=vision_model,
        embedding_model=embedding_model,
        image_detail=image_detail,
    )
    soma_text, soma_usage = provider.describe(prompt, prepared["soma_frames"])
    g1_text, g1_usage = provider.describe(prompt, prepared["g1_frames"])
    result = {
        **base,
        "source_soma_literal": soma_text,
        "g1_literal": g1_text,
        "cosine_similarity": provider.cosine_similarity(soma_text, g1_text),
        "usage": {"source_soma": soma_usage, "g1": g1_usage},
    }
    (output / "RESULT.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_result_report(result, output / "REPORT.md")
    return result


def write_result_report(result: dict[str, Any], path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                f"# {result['motion']}",
                "",
                f"- Cosine similarity: **{result['cosine_similarity']:.4f}**",
                f"- Samples: {result['protocol']['samples']} synchronized front+side composites",
                f"- Vision model: `{result['protocol']['vision_model']}`",
                f"- Embedding model: `{result['protocol']['embedding_model']}`",
                "",
                "## Source SOMA description",
                "",
                result["source_soma_literal"],
                "",
                "## G1 description",
                "",
                result["g1_literal"],
                "",
                "## Visual inputs",
                "",
                "[Source SOMA contact sheet](inputs/soma/contact_sheet.jpg) | "
                "[G1 contact sheet](inputs/g1/contact_sheet.jpg) | "
                "[Source SOMA video](source_soma/soma_front_side.mp4)",
                "",
            ]
        ),
        encoding="utf-8",
    )
