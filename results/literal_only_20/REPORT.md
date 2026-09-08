# Literal-Only 20-Motion Evaluation

## Evaluation protocol

- Source: SeG BVH rendered as corrected SOMA mesh with anatomical finger mapping and no IK
- Target: retargeted G1 front and side videos
- Window: source-BVH action window mapped to both embodiments by normalized phase
- Input: 12 uniformly sampled synchronized front+side composites
- VLM: `gpt-5.6-sol`, high image detail, identical literal-only prompt
- Similarity: `text-embedding-3-large` cosine between independent SOMA and G1 descriptions
- No SeG motion name or description is given to the VLM

## Summary

- Total mean: **0.8100** across 20 motions
- Original 10 mean: **0.8042**
- ARMS_AKIMBO-1: **0.6966**
- Random 9 mean: **0.8290**
- Range: **0.6525–0.9210**
- Scores ≥0.75: **17/20**; ≥0.80: **12/20**; ≥0.85: **7/20**
- Random selection seed: `20260908` from 532 eligible motions

| Group | Motion | Cosine |
|---|---|---:|
| Existing 10 | 0060_BELLY_PREGNANT-1 | 0.7970 |
| Existing 10 | 0097_EYE_TELESCOPE-3 | 0.8723 |
| Existing 10 | 0104_FINGERS_AIR_QUOTES-1 | 0.8865 |
| Existing 10 | 0107_FINGERS_BECKON-1 | 0.8114 |
| Existing 10 | 0148_FIST_CLASP-2 | 0.8110 |
| Existing 10 | 0151_FIST_KNOCK-1 | 0.6758 |
| Existing 10 | 0316_HANDS_STEERING-1 | 0.8587 |
| Existing 10 | 0388_HAND_TOAST-1 | 0.8237 |
| Existing 10 | 0417_HEAD_SCRATCH-1 | 0.6525 |
| Existing 10 | 0444_NOSE_TOUCH-1 | 0.8535 |
| Akimbo | 0001_ARMS_AKIMBO-1 | 0.6966 |
| Random 9 | 0014_ARMS_FOLD-2 | 0.7987 |
| Random 9 | 0133_FINGERTIPS_KISS-3 | 0.8301 |
| Random 9 | 0201_FOREFINGER_EMPTY-1 | 0.7845 |
| Random 9 | 0202_FOREFINGER_EMPTY-2 | 0.9210 |
| Random 9 | 0256_FOREHEAD_SALUTE-3 | 0.8247 |
| Random 9 | 0263_FOREHEAD_WIPE-2 | 0.7701 |
| Random 9 | 0367_HAND_PURSE-2 | 0.7732 |
| Random 9 | 0368_HAND_PURSE_AROUND-1 | 0.8872 |
| Random 9 | 0489_PALM_HALT-1 | 0.8711 |

## Result interpretation

- The 20-motion mean is useful as a pilot alignment score under one frozen protocol.
- High cosine generally reflects matching active limbs, direction, body region, and temporal order.
- Cosine can remain high when a semantically important detail differs, such as forehead contact versus an overhead pose.
- Lower scores can also come from harmless wording differences, so this metric should be paired with relation-level or kinematic checks in the paper.
- Lowest scores were HEAD_SCRATCH-1 (0.6525), FIST_KNOCK-1 (0.6758), and ARMS_AKIMBO-1 (0.6966).

### Important qualitative cases

- `FOREFINGER_EMPTY-2` (0.9210): both observations agree on the left hand above the right hand and the same temporal order; this is a strong match.
- `FOREHEAD_WIPE-2` (0.7701): SOMA shows the hand against the forehead and eyes, while G1 is described as near the head and oscillating; contact and motion type differ.
- `FOREHEAD_SALUTE-3` (0.8247): SOMA is positioned near the forehead, but G1 reaches above the head. The high score is driven by the shared right-arm raise-and-hold pattern.
- `HAND_PURSE-2` (0.7732): source targets the mouth while G1 targets the forehead, showing that cosine does not isolate the target body region strongly enough.
- `ARMS_AKIMBO-1` (0.6966): the defining hands-on-hips and elbows-out relation matches visually, but extra head and recovery wording lowers the score.

## Motion-by-motion inspection

### 0060_BELLY_PREGNANT-1

- **Group:** Existing 10
- **Cosine:** 0.7970
- **Source SOMA:** Right arm bends and lifts forward across the abdomen, hand turning thumb-up with fingers curled, pauses before the pelvis, then lowers once as the torso tilts right.
- **G1:** The right arm bends once, lifting the forearm forward and diagonally across the torso to chest height, then lowers palm-up before straightening beside the hip.
- **Visuals:** [SOMA sheet](artifacts/0060_BELLY_PREGNANT-1/soma_contact_sheet.jpg) | [G1 sheet](artifacts/0060_BELLY_PREGNANT-1/g1_contact_sheet.jpg) | [SOMA video](artifacts/0060_BELLY_PREGNANT-1/source_soma.mp4)

### 0097_EYE_TELESCOPE-3

- **Group:** Existing 10
- **Cosine:** 0.8723
- **Source SOMA:** Both arms lift forward with elbows bent, bringing curved fingers together directly before the eyes, hold this position briefly, then lower apart toward the sides.
- **G1:** Both arms lift forward from the sides, elbows bending as curved hands converge in front of and above the forehead, briefly hold, then lower.
- **Visuals:** [SOMA sheet](artifacts/0097_EYE_TELESCOPE-3/soma_contact_sheet.jpg) | [G1 sheet](artifacts/0097_EYE_TELESCOPE-3/g1_contact_sheet.jpg) | [SOMA video](artifacts/0097_EYE_TELESCOPE-3/source_soma.mp4)

### 0104_FINGERS_AIR_QUOTES-1

- **Group:** Existing 10
- **Cosine:** 0.8865
- **Source SOMA:** Both hands rise forward to face level with elbows bent, repeatedly flexing and extending the index and middle fingers while held apart.
- **G1:** Both arms rise forward with elbows bent, holding hands in front of the face as the index and middle fingers repeatedly bend and straighten, then lower.
- **Visuals:** [SOMA sheet](artifacts/0104_FINGERS_AIR_QUOTES-1/soma_contact_sheet.jpg) | [G1 sheet](artifacts/0104_FINGERS_AIR_QUOTES-1/g1_contact_sheet.jpg) | [SOMA video](artifacts/0104_FINGERS_AIR_QUOTES-1/source_soma.mp4)

### 0107_FINGERS_BECKON-1

- **Group:** Existing 10
- **Cosine:** 0.8114
- **Source SOMA:** Right arm lifts forward from the side to eye level, with elbow slightly bent, wrist flexed and fingers hanging downward, pauses, then lowers.
- **G1:** The right arm lifts forward and bends, positioning a flexed wrist and downward-pointing fingers near the face, holds briefly, then lowers.
- **Visuals:** [SOMA sheet](artifacts/0107_FINGERS_BECKON-1/soma_contact_sheet.jpg) | [G1 sheet](artifacts/0107_FINGERS_BECKON-1/g1_contact_sheet.jpg) | [SOMA video](artifacts/0107_FINGERS_BECKON-1/source_soma.mp4)

### 0148_FIST_CLASP-2

- **Group:** Existing 10
- **Cosine:** 0.8110
- **Source SOMA:** Both forearms lift forward to chest height; the right wrist bends downward with curved fingers above the partially closed left hand, then both lower.
- **G1:** Both arms lift forward with elbows bent, forearms crossing before the upper chest; the right hand rises near the face as this pose is maintained.
- **Visuals:** [SOMA sheet](artifacts/0148_FIST_CLASP-2/soma_contact_sheet.jpg) | [G1 sheet](artifacts/0148_FIST_CLASP-2/g1_contact_sheet.jpg) | [SOMA video](artifacts/0148_FIST_CLASP-2/source_soma.mp4)

### 0151_FIST_KNOCK-1

- **Group:** Existing 10
- **Cosine:** 0.6758
- **Source SOMA:** Right arm bends upward and forward, bringing a closed fist near the shoulder, then extends forward as the hand opens and lowers.
- **G1:** The right arm lifts forward with the elbow bent, bringing gathered fingertips near the face; the pose is held briefly before the fingers spread and arm lowers.
- **Visuals:** [SOMA sheet](artifacts/0151_FIST_KNOCK-1/soma_contact_sheet.jpg) | [G1 sheet](artifacts/0151_FIST_KNOCK-1/g1_contact_sheet.jpg) | [SOMA video](artifacts/0151_FIST_KNOCK-1/source_soma.mp4)

### 0316_HANDS_STEERING-1

- **Group:** Existing 10
- **Cosine:** 0.8587
- **Source SOMA:** Both forearms lift forward to chest height with elbows bent, while the curled hands repeatedly alternate vertically, one hovering above the other.
- **G1:** Both arms lift forward with bent elbows, while the separated hands repeatedly alternate vertically in front of the torso, then both arms lower.
- **Visuals:** [SOMA sheet](artifacts/0316_HANDS_STEERING-1/soma_contact_sheet.jpg) | [G1 sheet](artifacts/0316_HANDS_STEERING-1/g1_contact_sheet.jpg) | [SOMA video](artifacts/0316_HANDS_STEERING-1/source_soma.mp4)

### 0388_HAND_TOAST-1

- **Group:** Existing 10
- **Cosine:** 0.8237
- **Source SOMA:** Right arm lifts forward from the side to shoulder height as the elbow straightens and fingers curl, briefly holds, then lowers again.
- **G1:** The right arm bends and lifts forward from beside the hip to shoulder height, pauses with an open hand, then lowers.
- **Visuals:** [SOMA sheet](artifacts/0388_HAND_TOAST-1/soma_contact_sheet.jpg) | [G1 sheet](artifacts/0388_HAND_TOAST-1/g1_contact_sheet.jpg) | [SOMA video](artifacts/0388_HAND_TOAST-1/source_soma.mp4)

### 0417_HEAD_SCRATCH-1

- **Group:** Existing 10
- **Cosine:** 0.6525
- **Source SOMA:** The right hand and forearm lift forward to rest against the right side of the head while the head tilts right and torso bends, hold, then lower.
- **G1:** Right arm lifts with elbow bent until the hand is slightly forward of and beside the face, thumb and index forming a ring, holds, then lowers.
- **Visuals:** [SOMA sheet](artifacts/0417_HEAD_SCRATCH-1/soma_contact_sheet.jpg) | [G1 sheet](artifacts/0417_HEAD_SCRATCH-1/g1_contact_sheet.jpg) | [SOMA video](artifacts/0417_HEAD_SCRATCH-1/source_soma.mp4)

### 0444_NOSE_TOUCH-1

- **Group:** Existing 10
- **Cosine:** 0.8535
- **Source SOMA:** The right arm bends and lifts forward, holding a curled hand just before the mouth for several moments, then lowers.
- **G1:** The right arm bends forward and upward, holding the hand close before the face as fingers shift from curled to partly extended, then lowers.
- **Visuals:** [SOMA sheet](artifacts/0444_NOSE_TOUCH-1/soma_contact_sheet.jpg) | [G1 sheet](artifacts/0444_NOSE_TOUCH-1/g1_contact_sheet.jpg) | [SOMA video](artifacts/0444_NOSE_TOUCH-1/source_soma.mp4)

### 0001_ARMS_AKIMBO-1

- **Group:** Akimbo
- **Cosine:** 0.6966
- **Source SOMA:** Both arms lift and bend forward until the splayed hands contact the waist, holding the elbows laterally while the head tilts left.
- **G1:** Both arms bend simultaneously, bringing open hands forward and inward onto the upper hips with elbows flared outward, maintaining contact, then extending downward.
- **Visuals:** [SOMA sheet](artifacts/0001_ARMS_AKIMBO-1/soma_contact_sheet.jpg) | [G1 sheet](artifacts/0001_ARMS_AKIMBO-1/g1_contact_sheet.jpg) | [SOMA video](artifacts/0001_ARMS_AKIMBO-1/source_soma.mp4)

### 0014_ARMS_FOLD-2

- **Group:** Random 9
- **Cosine:** 0.7987
- **Source SOMA:** Both arms lift forward, fold across the chest with forearms overlapping, and hold while the torso and head lean left and knees bend slightly.
- **G1:** Both arms bend and lift forward until the forearms overlap across the chest, with one open palm upright, maintaining the pose before lowering.
- **Visuals:** [SOMA sheet](artifacts/0014_ARMS_FOLD-2/soma_contact_sheet.jpg) | [G1 sheet](artifacts/0014_ARMS_FOLD-2/g1_contact_sheet.jpg) | [SOMA video](artifacts/0014_ARMS_FOLD-2/source_soma.mp4)

### 0133_FINGERTIPS_KISS-3

- **Group:** Random 9
- **Cosine:** 0.8301
- **Source SOMA:** Left arm bends to lift the hand near the mouth with index finger extended, briefly holds, then reaches forward as the palm turns upward and fingers open.
- **G1:** Left arm lifts forward, bends to hold the hand near the face with index and thumb extended, then straightens forward and lowers.
- **Visuals:** [SOMA sheet](artifacts/0133_FINGERTIPS_KISS-3/soma_contact_sheet.jpg) | [G1 sheet](artifacts/0133_FINGERTIPS_KISS-3/g1_contact_sheet.jpg) | [SOMA video](artifacts/0133_FINGERTIPS_KISS-3/source_soma.mp4)

### 0201_FOREFINGER_EMPTY-1

- **Group:** Random 9
- **Cosine:** 0.7845
- **Source SOMA:** Left arm lifts forward from the side to above the head with elbow bent and fingers spread as the head tilts toward it, then lowers once.
- **G1:** The left arm lifts forward and upward, bends to place the open palm close before the face, briefly holds, then lowers to the side.
- **Visuals:** [SOMA sheet](artifacts/0201_FOREFINGER_EMPTY-1/soma_contact_sheet.jpg) | [G1 sheet](artifacts/0201_FOREFINGER_EMPTY-1/g1_contact_sheet.jpg) | [SOMA video](artifacts/0201_FOREFINGER_EMPTY-1/source_soma.mp4)

### 0202_FOREFINGER_EMPTY-2

- **Group:** Random 9
- **Cosine:** 0.9210
- **Source SOMA:** The left arm lifts forward to head height with elbow bent and fingers curved, while the right hand rises close beneath it, then both lower.
- **G1:** The left arm lifts forward above head height with a curved open hand, then the right hand rises close beneath it, briefly holding before both lower.
- **Visuals:** [SOMA sheet](artifacts/0202_FOREFINGER_EMPTY-2/soma_contact_sheet.jpg) | [G1 sheet](artifacts/0202_FOREFINGER_EMPTY-2/g1_contact_sheet.jpg) | [SOMA video](artifacts/0202_FOREFINGER_EMPTY-2/source_soma.mp4)

### 0256_FOREHEAD_SALUTE-3

- **Group:** Random 9
- **Cosine:** 0.8247
- **Source SOMA:** The right arm lifts forward, bends at the elbow to position the open hand above and slightly forward of the forehead, holds, then lowers.
- **G1:** The right arm lifts forward once from the side to above the head, remains bent overhead with an open curved hand, then lowers.
- **Visuals:** [SOMA sheet](artifacts/0256_FOREHEAD_SALUTE-3/soma_contact_sheet.jpg) | [G1 sheet](artifacts/0256_FOREHEAD_SALUTE-3/g1_contact_sheet.jpg) | [SOMA video](artifacts/0256_FOREHEAD_SALUTE-3/source_soma.mp4)

### 0263_FOREHEAD_WIPE-2

- **Group:** Random 9
- **Cosine:** 0.7701
- **Source SOMA:** Left arm bends and lifts forward once, placing the spread hand against the forehead and eyes as the head tilts right, holds, then lowers.
- **G1:** Left arm lifts forward with the elbow bent, holding an open, outward-facing hand near the head that oscillates side-to-side before lowering.
- **Visuals:** [SOMA sheet](artifacts/0263_FOREHEAD_WIPE-2/soma_contact_sheet.jpg) | [G1 sheet](artifacts/0263_FOREHEAD_WIPE-2/g1_contact_sheet.jpg) | [SOMA video](artifacts/0263_FOREHEAD_WIPE-2/source_soma.mp4)

### 0367_HAND_PURSE-2

- **Group:** Random 9
- **Cosine:** 0.7732
- **Source SOMA:** Left arm bends upward and forward, bringing the partially curled hand close to the mouth, holds there briefly, then lowers back beside the torso.
- **G1:** Left arm bends and lifts forward until the open hand is held close before the forehead, then lowers back beside the torso.
- **Visuals:** [SOMA sheet](artifacts/0367_HAND_PURSE-2/soma_contact_sheet.jpg) | [G1 sheet](artifacts/0367_HAND_PURSE-2/g1_contact_sheet.jpg) | [SOMA video](artifacts/0367_HAND_PURSE-2/source_soma.mp4)

### 0368_HAND_PURSE_AROUND-1

- **Group:** Random 9
- **Cosine:** 0.8872
- **Source SOMA:** Both arms lift forward with elbows bent as the open, spread-fingered hands rise from waist to chest level and turn toward each other.
- **G1:** Both arms lift forward from the sides with elbows bent and open palms, briefly cross near the waist, then separate toward face level before lowering.
- **Visuals:** [SOMA sheet](artifacts/0368_HAND_PURSE_AROUND-1/soma_contact_sheet.jpg) | [G1 sheet](artifacts/0368_HAND_PURSE_AROUND-1/g1_contact_sheet.jpg) | [SOMA video](artifacts/0368_HAND_PURSE_AROUND-1/source_soma.mp4)

### 0489_PALM_HALT-1

- **Group:** Random 9
- **Cosine:** 0.8711
- **Source SOMA:** The right arm lifts forward to shoulder height, extending with the palm facing outward and fingers spread, holds briefly, then lowers.
- **G1:** The right arm lifts forward with elbow bent, raising an open, forward-facing palm to head height, holds briefly, then lowers to the side.
- **Visuals:** [SOMA sheet](artifacts/0489_PALM_HALT-1/soma_contact_sheet.jpg) | [G1 sheet](artifacts/0489_PALM_HALT-1/g1_contact_sheet.jpg) | [SOMA video](artifacts/0489_PALM_HALT-1/source_soma.mp4)
