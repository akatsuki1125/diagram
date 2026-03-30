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

EDITING_SYSTEM_PROMPT = r"""You are an expert at editing LaTeX/TikZ diagrams.

You are given:
1) the original TikZ code of a diagram,
2) the original diagram image, and
3) an annotated version of that diagram image containing visual edit instructions.

Use all inputs together:
- Use the original TikZ code and the original image to understand the structure and content of the diagram.
- Use the annotated image to identify the requested edits.
- Resolve ambiguities by referring to the original diagram (code + image) for the base structure and the annotated image for the intended modifications.

Apply the requested edits and produce LaTeX/TikZ code representing the final diagram after the edits have been applied.
Your output must describe only the final edited diagram, not the original diagram and not the editing process.

Return only a complete standalone LaTeX document that compiles the final edited diagram.
The output must:
- begin with \documentclass{{standalone}}
- include all required packages and TikZ libraries
- contain exactly one tikzpicture environment
- end with \end{{document}}

Do not include any explanation, reasoning, markdown, code fences, comments, or any text before or after the LaTeX document.
"""

USER_PROMPT = r"""Original TikZ code:
{original_tikz_code}
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

def edit_image_to_tikz(
    client: OpenAI,
    model: str,
    original_img_path: str,
    original_tikz_code: str,
    annotated_img_path: str,
):
    base64_original = encode_image(original_img_path)
    base64_annotated = encode_image(annotated_img_path)

    system_prompt = EDITING_SYSTEM_PROMPT
    prompt = USER_PROMPT.format(original_tikz_code=original_tikz_code)

    res = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": system_prompt}
                ],
            },
            {
                "role": "user",
                "content": [
                    {   "type": "text", 
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_original}"
                        },
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_annotated}"
                        },
                    },
                ],
            },
        ],
    )
    return strip_thinking(res.choices[0].message.content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--model", help="使用したい VLM の HF ID を指定してください．", default="Qwen/Qwen3-VL-4B-Instruct")
    parser.add_argument("--base_url", help="vllm server 実行時に設定した PORT を元に指定してください．")
    parser.add_argument("--api_key", help="vllm server 実行時に設定した key を指定してください．")
    parser.add_argument("--annotated_img_file", help="編集指示が載った annotated image のファイル名を 拡張子付きで指定してください．未指定時は --org_img_file と同じ名前を使用します．", type=str)
    parser.add_argument("--original_tikz_code", help="edit 時の original tikz code", type=str)
    parser.add_argument("--org_img_file", help="元の original image のファイル名を 拡張子付きで指定してください．", type=str)
    
    args = parser.parse_args()
    client = OpenAI(base_url=args.base_url, api_key=args.api_key)
    
    # MAP を利用して HF ID の取得
    resolved_model = resolve_model_name(args.model)
    
    org_img_file = args.org_img_file
    annotated_img_file = args.annotated_img_file or org_img_file

    org_img_path = f"data/org_images/{org_img_file}"
    annotated_img_path = f"data/excalidraw_2026_all_red_png/{annotated_img_file}"
    annotated_img_name = Path(annotated_img_path).stem
    
    # edit の実行
    tikz_code = edit_image_to_tikz(
        client=client,
        model=resolved_model,
        original_img_path=org_img_path,
        original_tikz_code=args.original_tikz_code,
        annotated_img_path=annotated_img_path
    )
    
    # edit して取得した tikz code の保存
    save_dir = Path("work") / "visual_instruction_editing" / args.model / "tikz_code_w_org_image_w_tikz_code"
    save_dir.mkdir(parents=True, exist_ok=True)
    edited_stem = annotated_img_name.replace("visual_instruction_", "visual_instruction_edited_")
    edited_filename = f"{edited_stem}.tex"
    save_path = save_dir / edited_filename
    save_path.write_text(tikz_code, encoding="utf-8")
    print(f"saved: {save_path}")      
    
    # client = OpenAI(base_url="http://localhost:7777/v1", api_key="vllm-openai-key")
