"""Change colors of non-image elements in an Excalidraw file to #e03131."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


RED_HEX = "#e03131"


def change_color(
    input_path: str | Path,
    output_path: str | Path,
    color: str = RED_HEX,
) -> int:
    """Update ``strokeColor`` of all non-image elements and write JSON output.

    Args:
            input_path: Path to an ``.excalidraw`` JSON file.
            color: Hex color string to apply.
            output_path: Output file path. Must be different from ``input_path``.

    Returns:
            Number of updated elements.
    """
    in_path = Path(input_path)
    out_path = Path(output_path)

    if in_path.resolve() == out_path.resolve():
        raise ValueError("output_path must be different from input_path")

    with in_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    elements = data.get("elements", [])
    updated_count = 0

    for element in elements:
        if element.get("type") == "image":
            continue
        if element.get("strokeColor") != color:
            element["strokeColor"] = color
            updated_count += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    return updated_count


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Set strokeColor to #e03131 for all non-image Excalidraw elements."
    )
    parser.add_argument("input", help="Path to the input .excalidraw file")
    parser.add_argument("output", help="Path to the output .excalidraw file")
    parser.add_argument(
        "--color",
        default=RED_HEX,
        help=f"Color to apply (default: {RED_HEX})",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        updated = change_color(args.input, args.output, args.color)
    except ValueError as exc:
        parser.error(str(exc))
    print(f"Updated {updated} non-image elements: {args.input} -> {args.output}")


if __name__ == "__main__":
    main()
