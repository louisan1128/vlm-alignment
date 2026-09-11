# Data

The local workspace contains all **542** prepared motion pairs in `g1_pairs/`.
Each pair is self-contained; files that were symbolic links in the earlier
workspace were copied as real files.

## Pair layout

```text
0001_ARMS_AKIMBO-1/
  01_G1_VIDEO.mp4
  01_G1_SIDE_VIDEO.mp4
  02_SOURCE_BVH.bvh
  03_SEG_DESCRIPTION.txt
  04_ACTION_PHASE.json
  04_SOURCE_BVH_MOTION_ENERGY.png
  05_SOURCE_BVH_FRONT_SIDE_VIDEO.mp4
  06_G1_VLM_INPUT_CONTACT_SHEET.jpg
```

The evaluator requires the first five listed files. The other files are useful
for manual inspection. `SeG_list.xlsx` and the SeG license agreement are also
included locally.

Large data is excluded by `.gitignore`. Compress this directory, upload it to
the chosen storage service, and record the URL in `DATA_DOWNLOAD_URL.txt`.

## Compact cross-embodiment set

`cross_embodiment_10/` is a small, Git-tracked input set for the current
Source SOMA, Ours G1/Alex, and Baseline G1/Alex comparison. Each motion stores
front and side videos for the four robot conditions; Source SOMA is read from
the left panel of the Ours G1 comparison render. `manifest.json` stores the
source-derived action-window phases, so preprocessing this set does not require
the full `g1_pairs/` archive.
