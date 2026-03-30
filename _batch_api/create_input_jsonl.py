"""
Batch API（OpenAI） を使って画像を処理させるための, リクエスト(jsonl)を作成する
"""

import argparse
import base64
import json
from pathlib import Path

from dotenv import load_dotenv

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
- begin with \documentclass{{standalone}}
- include all required packages and TikZ libraries
- contain exactly one tikzpicture environment
- end with \end{{document}}

Do not include any explanation, reasoning, markdown, code fences, comments, or any text before or after the LaTeX document.
"""

USER_PROMPT = r"""Original TikZ code:
{original_tikz_code}
"""


def encode_image_as_data_url(image_path: Path) -> str:
    """画像ファイルをBase64エンコードし、data URL形式の文字列として返す。

    Args:
        image_path (Path): エンコード対象の画像ファイルのパス。

    Returns:
        str: `data:<mime>;base64,<encoded>` 形式のデータURL文字列。

    Notes:
        - 拡張子が `.png` の場合は `image/png`、それ以外は `image/jpeg` として扱う。
    """
    ext = (
        image_path.suffix.lower()
    )  # lower()は対象の文字列を小文字にする, 拡張子（extension）
    if ext == ".png":
        mime = "image/png"
    else:
        # 既定は jpg/jpeg 扱い
        mime = "image/jpeg"
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def build_request_line_for_visual_instruction_w_org_image_w_org_tikz_code(
    custom_id: str,
    model: str,
    system_instruction: str,
    user_prompt: str,
    original_image_url: str,
    visual_instruction_image_url: str,
) -> dict:
    """Batch API用の1リクエスト分のJSONオブジェクトを構築する。

    システム指示とユーザープロンプトに加え、元画像と視覚的指示画像の2枚を入力として、
    モデルに対してキャプション生成や編集内容の解釈などの処理を行わせるためのリクエストを作成する。
    生成されたリクエストはBatch APIで使用するjsonlの1行として利用できる形式で返す。

    Args:
        custom_id (str): 各リクエストを識別する一意なID。
        model (str): 使用するモデル名。
        system_instruction (str): モデルに与えるシステム指示文。
        user_prompt (str): ユーザーからの追加指示や入力テキスト。
        original_image_url (str): 元画像のdata URL。
        visual_instruction_image_url (str): 視覚的指示画像のdata URL。

    Returns:
        dict: Batch API用のリクエストオブジェクト。
              `custom_id`, `method`, `url`, `body` を含む。

    Notes:
        - ユーザー入力にはテキストと2枚の画像（元画像・指示画像）を含める。
        - `/v1/responses` エンドポイントを前提としている。
        - `/v1/chat/completions` を使用する場合は `body` を `messages` 形式に変更する必要がある。
    """
    body = {
        "model": model,
        "input": [
            {"role": "system", "content": system_instruction},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "input_image",
                        "image_url": original_image_url,
                    },
                    {
                        "type": "input_image",
                        "image_url": visual_instruction_image_url,
                    },
                ],
            },
        ],
    }

    return {
        "custom_id": custom_id,
        "method": "POST",
        "url": "/v1/responses",  # Responses API を使う前提。chat/completionsなら body のキーが messages になります
        "body": body,
    }


def build_request_line_for_visual_instruction_w_org_image(
    custom_id: str,
    model: str,
    system_instruction: str,
    original_image_url: str,
    visual_instruction_image_url: str,
) -> dict:
    """Batch API用の1リクエスト分のJSONオブジェクトを構築する。

     元画像と視覚的指示画像の2枚を入力として、システム指示に基づきモデルへ
    処理（例：キャプション生成や編集内容の解釈など）を行わせるためのリクエストを作成し、
     Batch API形式の1行分データとして返す。

     Args:
         custom_id (str): 各リクエストを識別する一意なID。
         model (str): 使用するモデル名。
         system_instruction (str): モデルに与えるシステム指示文。
         original_image_url (str): 元画像のdata URL。
         visual_instruction_image_url (str): 視覚的指示画像のdata URL。

     Returns:
         dict: Batch API用のリクエストオブジェクト。
               `custom_id`, `method`, `url`, `body` を含む。

     Notes:
         - 2枚の画像（元画像・指示画像）を `input` に順番に含める。
         - `/v1/responses` エンドポイントを前提としている。
         - `/v1/chat/completions` を使用する場合は `body` を `messages` 形式に変更する必要がある。
    """
    body = {
        "model": model,
        "input": [
            {"role": "system", "content": system_instruction},
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        "image_url": original_image_url,
                    },
                    {
                        "type": "input_image",
                        "image_url": visual_instruction_image_url,
                    },
                ],
            },
        ],
    }

    return {
        "custom_id": custom_id,
        "method": "POST",
        "url": "/v1/responses",  # Responses API を使う前提。chat/completionsなら body のキーが messages になります
        "body": body,
    }


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
        default="gpt-5.4-mini",
    )

    args = parser.parse_args()

    model = args.model

    # system_instructionのタイプによって分岐
    ## visual insrtruction + org image
    if args.system_instruction_type == "visual_instruction_w_org_image":
        system_instruction = EDITING_SYSTEM_PROMPT_VISUAL_INSTRUCTION_W_ORG_IMAGE

        save_path = args.save_path

        metadata_path = args.metadata_path
        with (
            open(save_path, "a", encoding="utf-8") as f,
            open(metadata_path, "r") as f_metadata,
        ):
            for line in f_metadata:
                metadata_dict = json.loads(line)

                key = metadata_dict["key"]
                custom_id = f"{key}_{args.system_instruction_type}"

                original_image_url = encode_image_as_data_url(
                    Path(metadata_dict["org_image_path"])
                )
                visual_instruction_image_url = encode_image_as_data_url(
                    Path(metadata_dict["visual_instruction_image_path"])
                )
                json_file = build_request_line_for_visual_instruction_w_org_image(
                    custom_id,
                    model,
                    system_instruction,
                    original_image_url,
                    visual_instruction_image_url,
                )
                f.write(json.dumps(json_file, ensure_ascii=False) + "\n")

    ## visual insrtruction + org image + org tikz code
    elif (
        args.system_instruction_type == "visual_instruction_w_org_image_w_org_tikz_code"
    ):
        system_instruction = (
            EDITING_SYSTEM_PROMPT_VISUAL_INSTRUCTION_W_ORG_IMAGE_W_ORG_TIKZ_CODE
        )

        save_path = args.save_path

        metadata_path = args.metadata_path
        with (
            open(save_path, "a", encoding="utf-8") as f,
            open(metadata_path, "r", encoding="utf-8") as f_metadata,
        ):
            for line in f_metadata:
                metadata_dict = json.loads(line)

                key = metadata_dict["key"]
                custom_id = f"{key}_{args.system_instruction_type}"

                org_tikz_code_path = metadata_dict["org_tikz_code_path"]
                with open(org_tikz_code_path, "r", encoding="utf-8") as f_tikz_code:
                    original_tikz_code = f_tikz_code.read()
                    print(original_tikz_code)
                    user_prompt = USER_PROMPT.format(
                        original_tikz_code=original_tikz_code
                    )

                original_image_url = encode_image_as_data_url(
                    Path(metadata_dict["org_image_path"])
                )
                visual_instruction_image_url = encode_image_as_data_url(
                    Path(metadata_dict["visual_instruction_image_path"])
                )
                json_file = build_request_line_for_visual_instruction_w_org_image_w_org_tikz_code(
                    custom_id,
                    model,
                    system_instruction,
                    user_prompt,
                    original_image_url,
                    visual_instruction_image_url,
                )
                f.write(json.dumps(json_file, ensure_ascii=False) + "\n")
