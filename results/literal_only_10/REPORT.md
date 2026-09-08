# Literal-Only 10-Motion Evaluation

This is the frozen pilot result bundled with `VLM Alignment v2`.

## Protocol

- Corrected SOMA body and anatomical finger rendering; no IK
- Source-derived action window
- 12 synchronized front+side composites per embodiment
- Fixed 512 px neutral body height
- `gpt-5.6-sol` with high image detail
- One literal physical-motion sentence per VLM call
- `text-embedding-3-large` cosine between SOMA and G1 descriptions
- SeG name and description withheld from both VLM calls

## Overall result

- Previous three-field prompt literal mean: **0.7760**
- Literal-only prompt mean: **0.8042**
- Change: **+0.0282**

| Motion | Previous | Literal-only | Change |
|---|---:|---:|---:|
| 0060_BELLY_PREGNANT-1 | 0.7684 | 0.7970 | +0.0287 |
| 0097_EYE_TELESCOPE-3 | 0.7434 | 0.8723 | +0.1289 |
| 0104_FINGERS_AIR_QUOTES-1 | 0.9468 | 0.8865 | -0.0603 |
| 0107_FINGERS_BECKON-1 | 0.8251 | 0.8114 | -0.0136 |
| 0148_FIST_CLASP-2 | 0.7640 | 0.8110 | +0.0470 |
| 0151_FIST_KNOCK-1 | 0.6486 | 0.6758 | +0.0272 |
| 0316_HANDS_STEERING-1 | 0.7047 | 0.8587 | +0.1539 |
| 0388_HAND_TOAST-1 | 0.8330 | 0.8237 | -0.0093 |
| 0417_HEAD_SCRATCH-1 | 0.6772 | 0.6525 | -0.0247 |
| 0444_NOSE_TOUCH-1 | 0.8492 | 0.8535 | +0.0043 |

## Motion-by-motion inspection

### 0060_BELLY_PREGNANT-1

[SOMA sheet](contact_sheets/0060_BELLY_PREGNANT-1/soma.jpg) | [G1 sheet](contact_sheets/0060_BELLY_PREGNANT-1/g1.jpg) | [SOMA video](source_soma_videos/0060_BELLY_PREGNANT-1.mp4)

- **SOMA:** Right arm bends and lifts forward across the abdomen, hand turning thumb-up with fingers curled, pauses before the pelvis, then lowers once as the torso tilts right.
- **G1:** The right arm bends once, lifting the forearm forward and diagonally across the torso to chest height, then lowers palm-up before straightening beside the hip.
- **Cosine:** 0.7970

### 0097_EYE_TELESCOPE-3

[SOMA sheet](contact_sheets/0097_EYE_TELESCOPE-3/soma.jpg) | [G1 sheet](contact_sheets/0097_EYE_TELESCOPE-3/g1.jpg) | [SOMA video](source_soma_videos/0097_EYE_TELESCOPE-3.mp4)

- **SOMA:** Both arms lift forward with elbows bent, bringing curved fingers together directly before the eyes, hold this position briefly, then lower apart toward the sides.
- **G1:** Both arms lift forward from the sides, elbows bending as curved hands converge in front of and above the forehead, briefly hold, then lower.
- **Cosine:** 0.8723

### 0104_FINGERS_AIR_QUOTES-1

[SOMA sheet](contact_sheets/0104_FINGERS_AIR_QUOTES-1/soma.jpg) | [G1 sheet](contact_sheets/0104_FINGERS_AIR_QUOTES-1/g1.jpg) | [SOMA video](source_soma_videos/0104_FINGERS_AIR_QUOTES-1.mp4)

- **SOMA:** Both hands rise forward to face level with elbows bent, repeatedly flexing and extending the index and middle fingers while held apart.
- **G1:** Both arms rise forward with elbows bent, holding hands in front of the face as the index and middle fingers repeatedly bend and straighten, then lower.
- **Cosine:** 0.8865

### 0107_FINGERS_BECKON-1

[SOMA sheet](contact_sheets/0107_FINGERS_BECKON-1/soma.jpg) | [G1 sheet](contact_sheets/0107_FINGERS_BECKON-1/g1.jpg) | [SOMA video](source_soma_videos/0107_FINGERS_BECKON-1.mp4)

- **SOMA:** Right arm lifts forward from the side to eye level, with elbow slightly bent, wrist flexed and fingers hanging downward, pauses, then lowers.
- **G1:** The right arm lifts forward and bends, positioning a flexed wrist and downward-pointing fingers near the face, holds briefly, then lowers.
- **Cosine:** 0.8114

### 0148_FIST_CLASP-2

[SOMA sheet](contact_sheets/0148_FIST_CLASP-2/soma.jpg) | [G1 sheet](contact_sheets/0148_FIST_CLASP-2/g1.jpg) | [SOMA video](source_soma_videos/0148_FIST_CLASP-2.mp4)

- **SOMA:** Both forearms lift forward to chest height; the right wrist bends downward with curved fingers above the partially closed left hand, then both lower.
- **G1:** Both arms lift forward with elbows bent, forearms crossing before the upper chest; the right hand rises near the face as this pose is maintained.
- **Cosine:** 0.8110

### 0151_FIST_KNOCK-1

[SOMA sheet](contact_sheets/0151_FIST_KNOCK-1/soma.jpg) | [G1 sheet](contact_sheets/0151_FIST_KNOCK-1/g1.jpg) | [SOMA video](source_soma_videos/0151_FIST_KNOCK-1.mp4)

- **SOMA:** Right arm bends upward and forward, bringing a closed fist near the shoulder, then extends forward as the hand opens and lowers.
- **G1:** The right arm lifts forward with the elbow bent, bringing gathered fingertips near the face; the pose is held briefly before the fingers spread and arm lowers.
- **Cosine:** 0.6758

### 0316_HANDS_STEERING-1

[SOMA sheet](contact_sheets/0316_HANDS_STEERING-1/soma.jpg) | [G1 sheet](contact_sheets/0316_HANDS_STEERING-1/g1.jpg) | [SOMA video](source_soma_videos/0316_HANDS_STEERING-1.mp4)

- **SOMA:** Both forearms lift forward to chest height with elbows bent, while the curled hands repeatedly alternate vertically, one hovering above the other.
- **G1:** Both arms lift forward with bent elbows, while the separated hands repeatedly alternate vertically in front of the torso, then both arms lower.
- **Cosine:** 0.8587

### 0388_HAND_TOAST-1

[SOMA sheet](contact_sheets/0388_HAND_TOAST-1/soma.jpg) | [G1 sheet](contact_sheets/0388_HAND_TOAST-1/g1.jpg) | [SOMA video](source_soma_videos/0388_HAND_TOAST-1.mp4)

- **SOMA:** Right arm lifts forward from the side to shoulder height as the elbow straightens and fingers curl, briefly holds, then lowers again.
- **G1:** The right arm bends and lifts forward from beside the hip to shoulder height, pauses with an open hand, then lowers.
- **Cosine:** 0.8237

### 0417_HEAD_SCRATCH-1

[SOMA sheet](contact_sheets/0417_HEAD_SCRATCH-1/soma.jpg) | [G1 sheet](contact_sheets/0417_HEAD_SCRATCH-1/g1.jpg) | [SOMA video](source_soma_videos/0417_HEAD_SCRATCH-1.mp4)

- **SOMA:** The right hand and forearm lift forward to rest against the right side of the head while the head tilts right and torso bends, hold, then lower.
- **G1:** Right arm lifts with elbow bent until the hand is slightly forward of and beside the face, thumb and index forming a ring, holds, then lowers.
- **Cosine:** 0.6525

### 0444_NOSE_TOUCH-1

[SOMA sheet](contact_sheets/0444_NOSE_TOUCH-1/soma.jpg) | [G1 sheet](contact_sheets/0444_NOSE_TOUCH-1/g1.jpg) | [SOMA video](source_soma_videos/0444_NOSE_TOUCH-1.mp4)

- **SOMA:** The right arm bends and lifts forward, holding a curled hand just before the mouth for several moments, then lowers.
- **G1:** The right arm bends forward and upward, holding the hand close before the face as fingers shift from curled to partly extended, then lowers.
- **Cosine:** 0.8535

## Reading the result

The literal-only schema improved the pilot mean, especially for eye telescope
and steering. Head scratch and fist knock remain weak because the observed
body-part relation differs across source and G1. A high cosine should therefore
be treated as one alignment metric, not as a complete validity decision.
