# Agent Working Notes

## Scientific protocol

- The primary score compares a source-BVH SOMA description with a G1 description.
- Do not expose the SeG motion name or description to the VLM observation call.
- Keep source and G1 prompts, frame count, image detail, and embedding model identical.
- Sample only within the source-derived action window using normalized phase.
- Keep front and side views synchronized in every composite.
- Use one fixed sequence-level transform; never track or recenter each frame.
- Treat cosine as literal physical-motion alignment, not complete semantic proof.

## Current frozen defaults

- Samples: 12 uniform action-window frames.
- Source: corrected SOMA direct local-rotation transfer with anatomical fingers; no IK.
- Body height: 512 px; target foot y: 592 px.
- VLM: `gpt-5.6-sol`, high image detail, literal-only JSON schema.
- Embedding: `text-embedding-3-large`.

## Engineering rules

- Keep API keys only in `.env`; never commit credentials or raw response headers.
- Add new prompt versions instead of silently overwriting the frozen prompt.
- Save every run's prompt name, model names, sampling count, text outputs, cosine,
  token usage, contact sheets, and source render.
- Batch runs must resume from existing `RESULT.json` files.
- Verify changes first with `--sample-only` to avoid accidental API cost.
- Preserve vendored Kimodo attribution and the SeG data license.
