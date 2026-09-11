# VLM Motion-Text Alignment Experiments

## Objective

This project evaluates whether a retargeted robot motion preserves the visible
physical action of its source motion. The primary pilot metric is cosine
similarity between two independently generated captions:

```text
Source motion -> VLM literal caption --+
                                      +-> text-embedding-3-large cosine
Robot motion  -> VLM literal caption --+
```

The VLM never receives the SeG motion name or SeG description. This avoids
label leakage and prevents abstract or inconsistent dataset annotations from
forcing the expected answer.

## Frozen Protocol

1. Detect the action window from the source BVH.
2. Project the same normalized phase interval onto source and target videos.
3. Uniformly sample 12 synchronized phases from that interval.
4. Combine front and side views into one `1280x640` image per phase.
5. Apply a fixed body-height and image-position normalization per embodiment.
6. Generate one literal physical-motion caption with the same prompt and VLM.
7. Embed the captions with `text-embedding-3-large` and compute cosine similarity.

The main caption prompt is
[`motion_alignment_cross_embodiment_literal_v1.txt`](../prompts/motion_alignment_cross_embodiment_literal_v1.txt).
It prioritizes active body parts, direction, coordination, body-relative
position, and visible hand configuration. Semantic interpretations such as
"welcome" or "knocking on a door" are excluded because an unseen object or
social intent cannot be verified consistently across embodiments.

## Completed 20-Motion Pilot

The completed source-SOMA versus retargeted-G1 pilot used `gpt-5.6-sol`, high
image detail, and the frozen 12-frame protocol.

| Statistic | Result |
|---|---:|
| Motions | 20 |
| Mean cosine | **0.8100** |
| Minimum | 0.6525 |
| Maximum | 0.9210 |
| Score >= 0.75 | 17/20 |
| Score >= 0.80 | 12/20 |
| Score >= 0.85 | 7/20 |

The weakest cases were `HEAD_SCRATCH-1` (0.6525), `FIST_KNOCK-1` (0.6758),
and `ARMS_AKIMBO-1` (0.6966). Their captions show the main limitation of a
single sentence cosine: it may penalize harmless wording changes or remain high
while missing a critical contact or target-body-region error.

Full captions, scores, contact sheets, and source videos are in
[`results/literal_only_20/REPORT.md`](../results/literal_only_20/REPORT.md).

## Model-Tier Pilot

All tiers received the same ten motions, prompt, 12 front+side samples, and
high-detail setting.

| VLM | Mean cosine | Estimated vision cost for 10 motions |
|---|---:|---:|
| `gpt-5.6-sol` | 0.8042 | $1.1193 |
| `gpt-5.6-terra` | 0.8285 | $0.5455 |
| `gpt-5.6-luna` | 0.7744 | $0.0585 |

Terra's higher cosine did not consistently mean better observation: it often
produced shorter and coarser captions that were easier to match. Sol retained
more fine-grained hand and target-region details, so it remains the primary
observer for experiments where local retargeting errors matter.

## InternVideo2 Pilot

Direct source-caption-to-G1-video retrieval was tested as a possible
motion-text metric, including matched and mismatched pairs.

| Encoder | R@1 | Mean matched | Mean mismatch |
|---|---:|---:|---:|
| InternVideo2 Stage2-1B f4 | 10% | 0.2688 | 0.2616 |
| InternVideo2 CLIP-B14 f8 | 10% | 0.1354 | 0.1281 |

The matched and mismatched distributions were too close, and the correct match
was usually not ranked first. This pilot is therefore not used as the primary
metric for the current fine-grained gesture set.

## Automatic-Relation Pilot

A source-grounded question-and-answer evaluator was also tested on four
motions. It automatically generated body-part relations and verified them on
source and target inputs. The pilot exposed observation errors and unstable
method ordering; for example, `HEAD_SCRATCH-1` scored 25% for Existing G1 and
50% for Baseline despite the qualitative result. The experiment is retained as
future work, not as the frozen paper metric.

## Current Cross-Embodiment Comparison

The next evaluation compares five independently observed conditions for each
of ten motions:

```text
Source SOMA
Ours G1
Ours Alex
Baseline G1
Baseline Alex
```

The curated repository input is under `data/cross_embodiment_10/`. It contains
front and side comparison videos plus the source-derived action-window phases.
The source SOMA is extracted from the left panel of the supplied comparison
render; each robot is extracted from the right panel. Method names, motion
names, and renderer overlays are removed before VLM sampling.

| Motion | Action-window phase |
|---|---:|
| BELLY_RUB-3 | 0.058-0.889 |
| EYES_RING-2 | 0.076-0.964 |
| FINGERS_AIR_QUOTES-1 | 0.072-0.794 |
| FINGERS_BECKON-1 | 0.047-0.895 |
| FIST_CLASP-2 | 0.042-0.857 |
| FIST_KNOCK-1 | 0.070-0.794 |
| HANDS_STEERING-1 | 0.038-0.835 |
| HAND_TOAST-1 | 0.021-0.819 |
| HEAD_SCRATCH-1 | 0.047-0.915 |
| NOSE_TOUCH-1 | 0.015-0.900 |

Current status: preprocessing is complete, but no API calls have been made for
this five-way set. The final run requires 50 VLM calls and produces 40
source-to-target cosine comparisons. An additional 20 motions were inspected
locally for crop and normalization behavior; their 189 MB generated report is
intentionally excluded from Git.

Prepare the frozen inputs with:

```bash
PYTHONPATH=src python scripts/prepare_cross_embodiment_10.py --force
```

## Interpretation for the Paper

Caption cosine is suitable as a reproducible supporting measure of global
motion-text agreement under a frozen protocol. It should not be presented as a
complete semantic-preservation score. The paper should report it alongside
local relation/contact checks, collision, smoothness, and success rate. Repeated
captioning runs or a stability study are also needed before final reporting.
