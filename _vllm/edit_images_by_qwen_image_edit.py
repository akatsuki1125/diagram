import argparse
import base64

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
    "qwen3-vl-30b-a3b-thinking-fp8": "Qwen/Qwen3-VL-30B-A3B-Thinking-FP8",
    "qwen-image-edit": "Qwen/Qwen-Image-Edit"
}

EDITING_PROMPT = r"""Edit this diagram according to the instruction below.
Preserve the original layout, geometry, line quality, labels, and sharp edges.
Only make the requested change.

Instruction:
{edit_instruction}
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

def edit_image_to_png(client: OpenAI, model: str, edit_instruction: str, img_path: str):
    # Getting the Base64 string
    base64_image = encode_image(img_path)

    prompt = EDITING_PROMPT.format(edit_instruction=edit_instruction)
    
    res = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"
                }},
            ],
        }],
        extra_body={
            "height": 1024,
            "width": 1024,
            "negative_prompt": "blurry, noisy, grainy, distorted lines, redrawn layout, extra text",
            "num_inference_steps": 50,
            "guidance_scale": 5,
            "seed": 42,
        },
    )
    img_url = res.choices[0].message.content[0]["image_url"]["url"]
    return img_url


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--model", help="使用したい VLM の HF ID を指定してください．", default="Qwen/Qwen3-VL-4B-Instruct")
    parser.add_argument("--base_url", help="vllm server 実行時に設定した PORT を元に指定してください．")
    parser.add_argument("--api_key", help="vllm server 実行時に設定した key を指定してください．")
    parser.add_argument("--edit_instruction", help="edit 時の text instruction", type=str)
    parser.add_argument("--org_img_file", help="edit したい original image のファイル名を 拡張子付きで 指定してください．", type=str)
    
    args = parser.parse_args()
    client = OpenAI(base_url=args.base_url, api_key=args.api_key)
    
    # MAP を利用して HF ID の取得
    resolved_model = resolve_model_name(args.model)
    
    org_img_file = args.org_img_file
    org_img_path = f"data/org_images/{org_img_file}"
    org_img_name = Path(org_img_path).stem
    
    # edit の実行
    edited_img_url = edit_image_to_png(
        client=client,
        model=resolved_model,
        edit_instruction=args.edit_instruction,
        img_path=org_img_path
    )
    _, b64_data = edited_img_url.split(",", 1)

    
    # edit して取得した tikz code の保存
    save_dir = Path("work") / "text_instruction_editing" / args.model / "w_h_w"
    save_dir.mkdir(parents=True, exist_ok=True)
    edited_stem = org_img_name.replace("org", "edited")
    edited_filename = f"{edited_stem}.png"
    save_path = save_dir / edited_filename
    # save_path.write_text(tikz_code, encoding="utf-8")
    with open(save_path, "wb") as f:
        f.write(base64.b64decode(b64_data))
    print(f"saved: {save_path}")    
    
    # client = OpenAI(base_url="http://localhost:7777/v1", api_key="vllm-openai-key")
