#!/usr/bin/env bash
set -euo pipefail

INPUT_DIR="./data/excalidraw_20260325"
OUTPUT_DIR="./data/excalidraw_20260325_png"

mkdir -p "$OUTPUT_DIR"

docker run --platform linux/amd64 --rm \
  -v "$(realpath "$INPUT_DIR"):/input" \
  -v "$(realpath "$OUTPUT_DIR"):/output" \
  -w /input \
  my-excalirender \
  -s 2 \
  -r . -o /output