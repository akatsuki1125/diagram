#!/usr/bin/env bash
set -euo pipefail

INPUT_DIR="./data/excalidraw_20260325"
OUTPUT_DIR="./data/excalidraw_20260325_svg"

mkdir -p "$OUTPUT_DIR"

find "$INPUT_DIR" -type f -name '*.excalidraw' | while read -r f; do
  base="$(basename "$f" .excalidraw)"
  docker run --platform linux/amd64 --rm \
    -v "$(realpath "$INPUT_DIR"):/input" \
    -v "$(realpath "$OUTPUT_DIR"):/output" \
    jonarc06/excalirender \
    "/input/$(basename "$f")" -o "/output/${base}.svg"
done