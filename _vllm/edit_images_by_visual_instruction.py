import argparse

from textwrap import dedent
from pathlib import Path
from openai import OpenAI

from utils import encode_image

MODEL_NAME_MAP = {
    "qwen3-vl-4b-instruct": "Qwen/Qwen3-VL-4B-Instruct",
    "qwen3-vl-4b-thinking": "Qwen/Qwen3-VL-4B-Thinking",
    "qwen3-vl-8b-instruct": "Qwen/Qwen3-VL-8B-Instruct",
    "qwen3-vl-8b-thinking": "Qwen/Qwen3-VL-8B-Thinking",
    "qwen3-vl-32b-instruct": "Qwen/Qwen3-VL-32B-Instruct",
    "qwen3-vl-32b-thinking": "Qwen/Qwen3-VL-32B-Thinking",
    "qwen3-vl-30b-a3b-instruct": "Qwen/Qwen3-VL-30B-A3B-Instruct",
    "qwen3-vl-30b-a3b-thinking": "Qwen/Qwen3-VL-30B-A3B-Thinking",
    "qwen3-vl-30b-a3b-instruct-fp8": "Qwen/Qwen3-VL-30B-A3B-Instruct-FP8",
    "qwen3-vl-30b-a3b-thinking-fp8": "Qwen/Qwen3-VL-30B-A3B-Thinking-FP8"
}

EDITING_SYSTEM_PROMPT = r"""You are an expert at converting diagram images into LaTeX/TikZ.

You are given a single image of a diagram that already contains written edit instructions on it.
Interpret both:
1. the current diagram shown in the image, and
2. the edit instructions written in or overlaid on the image.

Apply the requested edits and produce LaTeX/TikZ code that represents the final diagram after those edits have been applied.
Your output must describe the edited final state of the diagram itself, not the original diagram and not the editing process.

Return only a complete standalone LaTeX document that compiles the final edited diagram.
The output must:
- begin with \documentclass{{standalone}}
- include all required packages and TikZ libraries
- contain exactly one tikzpicture environment
- end with \end{{document}}

Do not include any explanation, reasoning, markdown, code fences, comments, or any text before or after the LaTeX document.
"""

def strip_thinking(content: str) -> str:
    """<think>...</think> ブロックを除去し、その後に続くテキストのみを返す。"""
    marker = "</think>"
    idx = content.find(marker)
    if idx != -1:
        content = content[idx + len(marker):]
    return content.strip()


def resolve_model_name(name: str) -> str:
    key = name.strip().lower()
    return MODEL_NAME_MAP.get(key, name)

def edit_image_to_tikz(client: OpenAI, model: str, img_path: str):
    # Getting the Base64 string
    base64_image = encode_image(img_path)

    prompt = EDITING_SYSTEM_PROMPT
    
    res = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": [{"type": "text", "text": prompt}]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        },
                    },
                ],
            }
        ],
    )
    return strip_thinking(res.choices[0].message.content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--model", help="使用したい VLM の HF ID を指定してください．", default="Qwen/Qwen3-VL-4B-Instruct")
    parser.add_argument("--base_url", help="vllm server 実行時に設定した PORT を元に指定してください．")
    parser.add_argument("--api_key", help="vllm server 実行時に設定した key を指定してください．")
    parser.add_argument("--org_img_file", help="edit したい original image のファイル名を 拡張子付きで 指定してください．", type=str)
    
    args = parser.parse_args()
    client = OpenAI(base_url=args.base_url, api_key=args.api_key)
    
    # MAP を利用して HF ID の取得
    resolved_model = resolve_model_name(args.model)
    
    org_img_file = args.org_img_file
    org_img_path = f"data/excalidraw_2026_all_red_png/{org_img_file}"
    org_img_name = Path(org_img_path).stem
    
    # edit の実行
    tikz_code = edit_image_to_tikz(
        client=client,
        model=resolved_model,
        img_path=org_img_path
    )
    
    # edit して取得した tikz code の保存
    save_dir = Path("work") / "visual_instruction_editing" / args.model / "tikz_code"
    save_dir.mkdir(parents=True, exist_ok=True)
    edited_stem = org_img_name.replace("visual_instruction_", "visual_instruction_edited_")
    edited_filename = f"{edited_stem}.tex"
    save_path = save_dir / edited_filename
    save_path.write_text(tikz_code, encoding="utf-8")
    print(f"saved: {save_path}")    
    
    # client = OpenAI(base_url="http://localhost:7777/v1", api_key="vllm-openai-key")
