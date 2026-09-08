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
