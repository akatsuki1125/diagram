#!/usr/bin/env bash
set -euo pipefail

INPUT_DIR="./data/excalidraw_20260325"
OUTPUT_DIR="./data/excalidraw_2026_all_red"

mkdir -p "$OUTPUT_DIR"

for file in "$INPUT_DIR"/*.excalidraw; 
do
    base_name="$(basename "$file")"
    python ./_excalidraw/preprocess/recolor.py "$file" "$OUTPUT_DIR/$base_name"
done
