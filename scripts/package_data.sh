#!/usr/bin/env bash
set -euo pipefail

project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
archive=${1:-"$project_root/vlm_alignment_v2_data.tar.gz"}

tar -C "$project_root" -czf "$archive" \
  data/g1_pairs \
  data/SeG_list.xlsx \
  data/License\ Agreement\ for\ MOCCA\ Semantic\ Gesture\ Dataset.pdf

printf 'Created %s\n' "$archive"
