"""
Batch API（OpenAI） を使って画像を処理させるための, リクエスト(jsonl)を作成する
"""

import argparse
import base64
import json
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image

EDITING_SYSTEM_PROMPT_VISUAL_INSTRUCTION_W_ORG_IMAGE = r"""You are an expert at converting diagram images into LaTeX/TikZ.

You are given two images of the same diagram:
1. the original diagram image, before any edit instructions were added, and
2. an annotated version of that same diagram image containing written edit instructions.

Use both images together:
- Use the original image to understand the diagram clearly without overlaid markings.
- Use the annotated image to identify the requested edits.
- Use both the original image to capture the underlying content and the annotated image to understand the intended modifications.

Apply the requested edits and produce LaTeX/TikZ code that represents the final diagram after those edits have been applied.
Your output must describe the edited final state of the diagram itself, not the original diagram and not the editing process.

Return only a complete standalone LaTeX document that compiles the final edited diagram.
The output must:
- begin with \documentclass{standalone}
- include all required packages and TikZ libraries
- contain exactly one tikzpicture environment
- end with \end{document}

Do not include any explanation, reasoning, markdown, code fences, comments, or any text before or after the LaTeX document.
"""

EDITING_SYSTEM_PROMPT_VISUAL_INSTRUCTION_W_ORG_IMAGE_W_ORG_TIKZ_CODE = r"""You are an expert at editing LaTeX/TikZ diagrams.

You are given:
1. the original TikZ code of a diagram,
2. the original diagram image, and
3. an annotated version of that diagram image containing visual edit instructions.

Use all inputs together:
- Use the original TikZ code and the original image to understand the structure and content of the diagram.
- Use the annotated image to identify the requested edits.
- Use both the original image to capture the underlying content and the annotated image to understand the intended modifications.

Apply the requested edits and produce LaTeX/TikZ code representing the final diagram after the edits have been applied.
Your output must describe only the final edited diagram, not the original diagram and not the editing process.

Return only a complete standalone LaTeX document that compiles the final edited diagram.
The output must:
- begin with \documentclass{standalone}
- include all required packages and TikZ libraries
- contain exactly one tikzpicture environment
- end with \end{document}

Do not include any explanation, reasoning, markdown, code fences, comments, or any text before or after the LaTeX document.
"""

USER_PROMPT = r"""Original TikZ code:
{original_tikz_code}
"""


def encode_image_base64(path: Path, max_dim: int = 7900) -> str | None:
    if not path.exists():
        return None

    with Image.open(path) as img:
        # Claude API has an image dimension limit (8000px). Resize oversized images.
        w, h = img.size
        long_edge = max(w, h)
        if long_edge > max_dim:
            scale = max_dim / long_edge
            new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        buffer = BytesIO()
        img.save(buffer, format="PNG")

    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def build_request_line_for_visual_instruction_w_org_image(
    custom_id: str,
    model: str,
    system_instruction: str,
    original_image_data: str,
    visual_instruction_image_data: str,
) -> dict:
    """Batch API用の1リクエスト分のJSONオブジェクトを構築する。

    元画像と視覚的指示画像の2枚をBase64エンコードされたデータとして入力し、
    システム指示に基づいてモデルに処理（例：キャプション生成や編集内容の解釈など）
    を行わせるためのリクエストを作成する。
    生成されたオブジェクトはBatch APIで使用するjsonlの1行として利用できる形式で返す。

    Args:
        custom_id (str): 各リクエストを識別する一意なID。
        model (str): 使用するモデル名。
        system_instruction (str): モデルに与えるシステム指示文。
        original_image_data (str): 元画像のBase64エンコード済みデータ。
        visual_instruction_image_data (str): 視覚的指示画像のBase64エンコード済みデータ。

    Returns:
        dict: Batch API用のリクエストオブジェクト。
              `key`（リクエストID）と `request`（APIリクエスト本体）を含む。

    Notes:
        - 画像は `inlineData` として渡され、`mimeType` は `"image/png"` を想定している。
        - 2枚の画像は `contents.parts` 内に順番に含められる。
    """
    request = {
        "custom_id": custom_id,
        "params": {
            "model": model,
            "max_tokens": 8192,
            "system": system_instruction,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": original_image_data,
                            },
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": visual_instruction_image_data,
                            },
                        },
                    ],
                }
            ],
        },
    }

    return request


def build_request_line_for_visual_instruction_w_org_image_w_org_tikz_code(
    custom_id: str,
    model: str,
    system_instruction: str,
    user_prompt: str,
    original_image_data: str,
    visual_instruction_image_data: str,
) -> dict:
    """Batch API用の1リクエスト分のJSONオブジェクトを構築する。

    システム指示とユーザープロンプトに加え、元画像と視覚的指示画像の2枚を
    Base64エンコードされたデータとして入力し、モデルに対してキャプション生成や
    編集内容の解釈などの処理を行わせるためのリクエストを作成する。
    生成されたオブジェクトはBatch APIで使用するjsonlの1行として利用できる形式で返す。

    Args:
        custom_id (str): 各リクエストを識別する一意なID。
        model (str): 使用するモデル名。
        system_instruction (str): モデルに与えるシステム指示文。
        user_prompt (str): ユーザーからの追加指示や入力テキスト。
        original_image_data (str): 元画像のBase64エンコード済みデータ（data URLではなく純粋なBase64文字列）。
        visual_instruction_image_data (str): 視覚的指示画像のBase64エンコード済みデータ。

    Returns:
        dict: Batch API用のリクエストオブジェクト。
              `key`（リクエストID）と `request`（APIリクエスト本体）を含む。

    Notes:
        - 画像は `inlineData` として渡され、`mimeType` は `"image/png"` を想定している。
        - テキストは `parts` 内の `"text"` フィールドとして渡される。
    """
    request = {
        "custom_id": custom_id,
        "params": {
            "model": model,
            "max_tokens": 8192,
            "system": system_instruction,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": original_image_data,
                            },
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": visual_instruction_image_data,
                            },
                        },
                    ],
                }
            ],
        },
    }

    return request


def save_json_to_jsonl(json_file: dict, save_path: str):
    """
    jsonファイルとそれを保存する先のjsonlファイルまでのパスを渡すと, jsonをjsonlファイルの1行として保存してくれる
    """
    with open(save_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(json_file, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--metadata_path", help="処理したいメタデータのパス", required=True
    )
    parser.add_argument(
        "--system_instruction_type",
        help="choices=[visual_instruction_w_org_image, visual_instruction_w_org_image_w_org_tikz_code]",
        required=True,
        choices=[
            "visual_instruction_w_org_image",
            "visual_instruction_w_org_image_w_org_tikz_code",
        ],
    )
    parser.add_argument(
        "--save_path", help="保存したいjsonlまでのパスを指定してください", required=True
    )
    parser.add_argument(
        "--model",
        help="抽出するときに使用したいモデルを指定してください",
        default="claude-opus-4-6",
    )

    args = parser.parse_args()

    model = args.model

    # system_instructionのタイプによって分岐
    ## visual insrtruction + org image
    if args.system_instruction_type == "visual_instruction_w_org_image":
        system_instruction = EDITING_SYSTEM_PROMPT_VISUAL_INSTRUCTION_W_ORG_IMAGE

        save_path = Path(args.save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        metadata_path = args.metadata_path
        with (
            open(save_path, "a", encoding="utf-8") as f,
            open(metadata_path, "r", encoding="utf-8") as f_metadata,
        ):
            for line in f_metadata:
                metadata_dict = json.loads(line)

                key = metadata_dict["key"]
                custom_id = f"{key}_{args.system_instruction_type}"

                original_image_data = encode_image_base64(
                    Path(metadata_dict["org_image_path"])
                )
                visual_instruction_image_data = encode_image_base64(
                    Path(metadata_dict["visual_instruction_image_path"])
                )
                json_file = build_request_line_for_visual_instruction_w_org_image(
                    custom_id,
                    model,
                    system_instruction,
                    original_image_data,
                    visual_instruction_image_data,
                )
                f.write(json.dumps(json_file, ensure_ascii=False) + "\n")

    ## visual insrtruction + org image + org tikz code
    elif (
        args.system_instruction_type == "visual_instruction_w_org_image_w_org_tikz_code"
    ):
        system_instruction = (
            EDITING_SYSTEM_PROMPT_VISUAL_INSTRUCTION_W_ORG_IMAGE_W_ORG_TIKZ_CODE
        )

        save_path = Path(args.save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        metadata_path = args.metadata_path
        with (
            open(save_path, "a", encoding="utf-8") as f,
            open(metadata_path, "r", encoding="utf-8") as f_metadata,
        ):
            for line in f_metadata:
                metadata_dict = json.loads(line)

                key = metadata_dict["key"]
                custom_id = f"{key}"

                org_tikz_code_path = metadata_dict["org_tikz_code_path"]
                with open(org_tikz_code_path, "r", encoding="utf-8") as f_tikz_code:
                    original_tikz_code = f_tikz_code.read()
                    # print(original_tikz_code)
                    user_prompt = USER_PROMPT.format(
                        original_tikz_code=original_tikz_code
                    )

                original_image_data = encode_image_base64(
                    Path(metadata_dict["org_image_path"])
                )
                visual_instruction_image_data = encode_image_base64(
                    Path(metadata_dict["visual_instruction_image_path"])
                )
                json_file = build_request_line_for_visual_instruction_w_org_image_w_org_tikz_code(
                    custom_id,
                    model,
                    system_instruction,
                    user_prompt,
                    original_image_data,
                    visual_instruction_image_data,
                )
                f.write(json.dumps(json_file, ensure_ascii=False) + "\n")
