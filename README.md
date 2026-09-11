# VLM Alignment v2

SeG source BVH와 retargeted Unitree G1 motion이 같은 물리적 동작을
표현하는지 VLM description cosine similarity로 평가하는 독립 프로젝트다.

## Current pipeline

```text
Source SeG BVH
  -> corrected SOMA mesh rendering (front + side, no IK)
  -> source-derived action window
  -> 12 uniformly sampled phases
  -> fixed body-height normalization
  -> literal-only VLM description
                                      -> text-embedding-3-large cosine
Retargeted G1 front + side videos
  -> same normalized action window
  -> 12 uniformly sampled phases
  -> fixed body-height normalization
  -> identical literal-only VLM description
```

The SeG name and description are retained as metadata, but they are not shown
to the VLM and are not used in the primary cosine score. This prevents an
inconsistent or abstract SeG annotation from leaking the expected answer.

## Results

The frozen 20-motion evaluation, including per-motion descriptions, cosine
scores, contact sheets, and source SOMA videos, is available in
[`results/literal_only_20/REPORT.md`](results/literal_only_20/REPORT.md).

- Mean cosine similarity: **0.8100**
- Motions scoring at least 0.75: **17/20**
- Vision model: `gpt-5.6-sol`
- Embedding model: `text-embedding-3-large`

The consolidated protocol, experiment history, rejected pilots, and current
five-way Ours/Baseline preparation are documented in
[`docs/EXPERIMENT_REPORT.md`](docs/EXPERIMENT_REPORT.md).

## Data

The local `data/g1_pairs/` directory contains 542 complete pairs. See
[`data/README.md`](data/README.md) for the required file layout. Bulk data is
ignored by Git and distributed as a
[separate Dropbox archive](https://www.dropbox.com/scl/fi/uhk90uh6biwdtrep8895m/vlm_alignment_v2_data.tar.gz?rlkey=3j5rl9l6iit5wir8nkvygogmp&st=icqt4p22&dl=1).

Download and extract it from the project root:

```bash
curl -L 'https://www.dropbox.com/scl/fi/uhk90uh6biwdtrep8895m/vlm_alignment_v2_data.tar.gz?rlkey=3j5rl9l6iit5wir8nkvygogmp&st=icqt4p22&dl=1' -o vlm_alignment_v2_data.tar.gz
tar -xzf vlm_alignment_v2_data.tar.gz
python scripts/validate_data.py
```

Expected SHA-256:
`13355dc8307bd571b78549e8b98f99a7ba7f231ad8b521008bdf465b97445b5f`.

The repository also includes the compact `data/cross_embodiment_10/` set used
to prepare the current Source SOMA, Ours G1/Alex, and Baseline G1/Alex
comparison. It does not require the full 542-motion archive.

## Setup

Python 3.10 or later and `ffmpeg` are required.

```bash
cd vlm_alignment_v2
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Put the OpenAI key in `.env`, then load it in the current shell:

```bash
set -a
source .env
set +a
```

## Run

List available motions:

```bash
vlm-align list | head
vlm-align list --pattern '*STEERING*'
```

Validate the complete local data copy:

```bash
python scripts/validate_data.py
```

Prepare one motion without spending API tokens:

```bash
vlm-align evaluate data/g1_pairs/0316_HANDS_STEERING-1 --sample-only
```

Run the complete evaluation:

```bash
vlm-align evaluate data/g1_pairs/0316_HANDS_STEERING-1
```

Run a resumable batch:

```bash
vlm-align batch --pattern '*FINGERS*' --limit 10
```

Prepare the current five-way comparison without API calls:

```bash
PYTHONPATH=src python scripts/prepare_cross_embodiment_10.py --force
```

Render only a source BVH:

```bash
vlm-align render \
  data/g1_pairs/0316_HANDS_STEERING-1/02_SOURCE_BVH.bvh \
  outputs/steering_render
```

Each evaluated motion produces:

```text
outputs/<motion>/
  source_soma/soma_front_side.mp4
  inputs/soma/frame_*.jpg
  inputs/soma/contact_sheet.jpg
  inputs/g1/frame_*.jpg
  inputs/g1/contact_sheet.jpg
  RESULT.json
  REPORT.md
```

The first SOMA render is CPU-heavy and took about two minutes in the local
smoke test. The generated MP4 is cached under the motion output directory, so
later evaluations of the same output reuse it unless `--force-render` is used.

## Frozen evaluation settings

| Item | Setting |
|---|---|
| Source representation | SOMA mesh, anatomical finger mapping, direct local rotations, no IK |
| Views | synchronized front + side |
| Action window | computed from source BVH and mapped by normalized phase |
| Sampling | 12 uniform frames inside the action window |
| Framing | 512 px neutral body height, fixed per-sequence transform |
| Prompt | `prompts/motion_alignment_literal_only_v1.txt` |
| VLM | `gpt-5.6-sol`, high image detail |
| Embedding | `text-embedding-3-large` |
| Primary score | cosine(source SOMA literal, G1 literal) |

## Interpretation

The score measures agreement between two independently observed literal motion
descriptions. It is useful for ranking retargeting methods under one frozen
protocol, but it is not by itself proof of contact, collision safety, dynamic
feasibility, or full semantic preservation. Paper evaluation should report
those metrics separately and include repeated VLM runs or a stability study.

## Reproducibility notes

- Source and G1 receive the same prompt, frame count, model, and image detail.
- Front and side frames in each image are synchronized.
- Normalization is fixed for the sequence, so image-plane motion is preserved.
- Existing `RESULT.json` files make batch evaluation resumable.
- Batch errors are recorded per motion and do not discard completed results.
- Use `--force` for a batch rerun and `--force-render` only when the source
  renderer changed.

## Third-party material

The minimal SOMA skeleton and skin implementation under `third_party/kimodo`
comes from NVIDIA Kimodo and retains its Apache-2.0 license. SeG data remains
subject to the license agreement included under `data/`; check its terms before
redistributing the data archive.
