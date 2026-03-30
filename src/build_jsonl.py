import argparse
import json
from typing import Tuple
from pathlib import Path

REF_JSONL_PATH = "data/visual_instruction/nouhin_data_20260325.jsonl"
SAVE_JSONL_PATH = "data/metadata/edit_metadata.jsonl"


def parse_identifier(identifier: str) -> Tuple[str, str, str]:
    """{record_id}_{edit_type}_{num_edit_instruction}_edit_0となっているkeyからそれぞれを取得する関数

    Args:
        identifier (str): 例） 00026602_REMOVE_3_edit_0

    Returns:
        Tuple[str, str, str]: record_id, edit_type, num_edit_instruction
    """

    record_id, edit_type, num_edit_instruction, _, _ = identifier.split("_")
    return record_id, edit_type, num_edit_instruction


def main():
    Path(SAVE_JSONL_PATH).parent.mkdir(parents=True, exist_ok=True)

    # jsonlを読み込んで, 各line(json)をdictに直して, 修正していく
    with open(REF_JSONL_PATH, "r") as f:
        for line in f:
            save_json_dict = dict()  # 新しくjsonlに保存する用のjson_dict
            read_json_dict = json.loads(line)  # 参照jsonlから読み込んだjson_dict

            save_json_dict["key"] = read_json_dict["key"]

            record_id, edit_type, num_edit_instruction = parse_identifier(
                save_json_dict["key"]
            )

            save_json_dict["record_id"] = record_id
            save_json_dict["edit_type"] = edit_type
            save_json_dict["num_edit_instruction"] = num_edit_instruction

            save_json_dict["org_image_path"] = f"data/org_images/{record_id}.png"
            visual_instruction_filename = Path(
                read_json_dict["instruction_visual"]
            ).stem
            save_json_dict["visual_instruction_image_path"] = (
                f"data/excalidraw_2026_all_red_png/{visual_instruction_filename}.png"
            )
            save_json_dict["org_tikz_code_path"] = f"data/org_tikz_code/{record_id}.tex"

            save_json_dict["text_instruction"] = read_json_dict["edit_instruction"]

            with open(SAVE_JSONL_PATH, "a") as f_save:
                json.dump(save_json_dict, f_save, ensure_ascii=False)
                f_save.write("\n")


if __name__ == "__main__":
    main()
