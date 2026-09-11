# Project Handoff

Last updated: 2026-09-11

## Read This First

This file records the current research objective, frozen decisions, completed
work, and immediate next task. It is intentionally limited to information
needed to continue the project; exploratory local files are not authoritative.

## Research Context

This evaluator supports a paper about agent-based adaptive fine-grained local
motion refinement. The evaluator's responsibility is motion-text alignment:
measure whether a retargeted robot motion preserves the visible action of its
source SeG motion.

The paper compares Ours with agentic and non-agentic retargeting baselines. The
overall paper will separately report semantic preservation, collision,
smoothness, and success rate. Caption cosine is only the motion-text alignment
component, not a complete motion-quality metric.

## Current Primary Metric

Generate one independent literal caption from the source motion and one from
each robot motion, then embed the captions with `text-embedding-3-large` and
compute cosine similarity.

```text
Source SOMA frames -> VLM literal caption --+
                                           +-> cosine similarity
Robot frames       -> VLM literal caption --+
```

Do not provide the SeG motion name or SeG description to either observation.
The dataset descriptions vary between physical and abstract language and can
bias the VLM toward the expected class.

## Frozen Observation Protocol

- Detect the action window from the source BVH and store it as normalized phase.
- Project exactly that interval onto every source and robot rendition.
- Uniformly sample 12 phases strictly within the shared action window.
- Use synchronized front and side views in each temporal sample.
- Save each sample as one `1280x640` front-plus-side composite.
- Normalize body scale and screen position with one fixed transform per
  sequence. Never track or recenter individual frames.
- Remove renderer labels, method names, and motion names before VLM input.
- Use the same prompt, frame count, model, and image detail for every condition.
- Current VLM: `gpt-5.6-sol`, high image detail.
- Current prompt:
  `prompts/motion_alignment_cross_embodiment_literal_v1.txt`.
- Output: exactly one literal physical-motion sentence in JSON.
- Do not infer invisible objects, communicative intent, emotion, or dataset
  labels. Contact-specific verbs require visible temporal evidence.

Twelve frames are retained instead of 24 because the five-motion ablation found
that 24 frames did not improve the mean caption cosine and increased cost.
Literal-only output is retained because requesting semantic interpretation made
captions less stable and could reward the same incorrect action guess.

## Completed Work

### Frozen 20-motion pilot

- Source: corrected SOMA rendering of SeG BVH.
- Target: retargeted G1 front and side videos.
- Mean cosine: `0.8100`.
- Range: `0.6525` to `0.9210`.
- Full report: `results/literal_only_20/REPORT.md`.
- Structured results: `results/literal_only_20/RESULTS.json`.

This pilot established that caption cosine is useful for broad agreement, but
it can miss fine contact or target-region errors and is sensitive to wording.
It should be reported with local semantic checks, not alone.

### Current five-way comparison preparation

The next experiment compares the same source with four targets:

1. Source SOMA
2. Ours G1
3. Ours Alex
4. Baseline G1
5. Baseline Alex

The compact inputs are committed under `data/cross_embodiment_10/`. Each motion
contains front and side videos for the four robot conditions. Source SOMA is
read from the left panel of the Ours G1 comparison render. The right panel is
the robot. Overlay text is masked before sampling.

The ten main motions are:

- `BELLY_RUB-3`
- `EYES_RING-2`
- `FINGERS_AIR_QUOTES-1`
- `FINGERS_BECKON-1`
- `FIST_CLASP-2`
- `FIST_KNOCK-1`
- `HANDS_STEERING-1`
- `HAND_TOAST-1`
- `HEAD_SCRATCH-1`
- `NOSE_TOUCH-1`

`data/cross_embodiment_10/manifest.json` contains their source action-window
phases. `scripts/prepare_cross_embodiment_10.py` creates the normalized samples,
contact sheets, action-window videos, and preparation report.

Current status: preprocessing was validated with a one-motion smoke test. No
OpenAI API call has been made for this five-way set. A complete run will need 50
VLM caption calls and 40 source-to-target embedding comparisons.

Twenty additional motions were prepared locally only for visual crop and scale
inspection. Their generated `outputs/` content was deliberately not committed.

## Immediate Next Task

Implement or adapt a resumable five-way evaluator that consumes the prepared
directories and:

1. calls the VLM once for each of the five conditions;
2. validates `{"literal_motion":"..."}`;
3. embeds all five captions;
4. computes Source SOMA versus each of the four robot captions;
5. records token usage, model settings, prompt hash, image hashes, captions,
   and cosine scores;
6. writes one compact JSON result and one readable report;
7. resumes completed calls without spending tokens again.

Run a sample-only preparation first. Do not launch the 50 API calls unless the
user explicitly authorizes the cost.

## Reproduction

```bash
git pull origin main
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
# Add OPENAI_API_KEY to .env

PYTHONPATH=src python scripts/prepare_cross_embodiment_10.py --force
```

The complete historical 542-pair dataset is optional for the current ten-motion
preparation. Its download link and checksum are in `README.md`.

## Files To Trust

- `AGENTS.md`: scientific and engineering rules.
- `HANDOFF.md`: current state and next task.
- `README.md`: setup and normal CLI usage.
- `docs/EXPERIMENT_REPORT.md`: concise experiment record.
- `prompts/motion_alignment_cross_embodiment_literal_v1.txt`: current prompt.
- `scripts/prepare_cross_embodiment_10.py`: current five-way preprocessing.
- `data/cross_embodiment_10/manifest.json`: selected motions and phase windows.

## Local-Only Work

The previous computer may still contain untracked relation, InternVideo2,
X-CLIP, DMR, prompt-ablation, and report-building scripts. They were exploratory
and were intentionally excluded from the clean GitHub handoff. Do not assume
they exist on a fresh clone and do not make them dependencies of the primary
pipeline without an explicit decision.

## Prompt For A New Coding Session

Use the following message after opening the cloned repository:

```text
Read AGENTS.md and HANDOFF.md first. Continue the five-way cross-embodiment
motion-text alignment evaluator from the documented current state. Preserve the
frozen protocol, inspect existing code before editing, and do not make API calls
until I explicitly approve them.
```
