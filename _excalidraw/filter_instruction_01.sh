#!/usr/bin/env bash
set -euo pipefail

INPUT_DIR="./data/excalidraw_20260325_png"
OUTPUT_DIR="./data/excalidraw_20260325_png_01"

mkdir -p "$OUTPUT_DIR"

# ファイル名が{filename}_01.pngのようになっているものを集めてcopyする
for file in "${INPUT_DIR}"/*01.png;
do
    cp "${file}" "${OUTPUT_DIR}"
done