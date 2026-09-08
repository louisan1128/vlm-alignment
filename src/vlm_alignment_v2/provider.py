from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from .models import SampledFrame


LITERAL_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {"literal_motion": {"type": "string"}},
    "required": ["literal_motion"],
    "additionalProperties": False,
}


class OpenAIProvider:
    def __init__(
        self,
        *,
        vision_model: str = "gpt-5.6-sol",
        embedding_model: str = "text-embedding-3-large",
        image_detail: str = "high",
    ) -> None:
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not set. Copy .env.example to .env and load it.")
        from openai import OpenAI

        self.client = OpenAI()
        self.vision_model = vision_model
        self.embedding_model = embedding_model
        self.image_detail = image_detail

    @staticmethod
    def _data_url(path: Path) -> str:
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"

    def _describe_once(
        self, prompt: str, frames: Sequence[SampledFrame]
    ) -> tuple[str, dict[str, Any]]:
        content: list[dict[str, Any]] = [{"type": "input_text", "text": prompt}]
        for frame in frames:
            content.extend(
                [
                    {
                        "type": "input_text",
                        "text": (
                            f"Chronological frame {frame.order}/{len(frames)}; "
                            f"action-window phase {frame.window_phase:.3f}."
                        ),
                    },
                    {
                        "type": "input_image",
                        "image_url": self._data_url(frame.path),
                        "detail": self.image_detail,
                    },
                ]
            )
        response = self.client.responses.create(
            model=self.vision_model,
            input=[{"role": "user", "content": content}],
            max_output_tokens=1024,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "literal_motion_description",
                    "description": "One directly observed physical-motion sentence.",
                    "schema": LITERAL_SCHEMA,
                    "strict": True,
                }
            },
        )
        if str(getattr(response, "status", "")) == "incomplete":
            reason = getattr(getattr(response, "incomplete_details", None), "reason", "unknown")
            raise RuntimeError(f"OpenAI response was incomplete: {reason}")
        payload = json.loads(str(getattr(response, "output_text", "")).strip())
        usage = getattr(response, "usage", None)
        return str(payload["literal_motion"]).strip(), {
            "response_id": getattr(response, "id", None),
            "status": getattr(response, "status", None),
            "input_tokens": getattr(usage, "input_tokens", None),
            "output_tokens": getattr(usage, "output_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
        }

    def describe(
        self, prompt: str, frames: Sequence[SampledFrame], retries: int = 3
    ) -> tuple[str, dict[str, Any]]:
        for attempt in range(retries):
            try:
                return self._describe_once(prompt, frames)
            except Exception:
                if attempt + 1 == retries:
                    raise
                time.sleep(3 * (attempt + 1))
        raise AssertionError("unreachable")

    def cosine_similarity(self, left: str, right: str) -> float:
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=[left, right],
            encoding_format="float",
        )
        ordered = sorted(response.data, key=lambda item: item.index)
        vectors = np.asarray([item.embedding for item in ordered], dtype=np.float64)
        vectors /= np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12)
        return float(np.dot(vectors[0], vectors[1]))
