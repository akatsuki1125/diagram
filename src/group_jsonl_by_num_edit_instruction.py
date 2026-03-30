"""JSONのnum_edit_instructionの数字によって, それぞれ別のjsonlに保存する"""

import json


def main():
    ALL_EDIT_METADATA_JSONL_PATH = "data/metadata/edit_metadata.jsonl"
    SAVE_EDIT_METADARA_1_JSONL_PATH = "data/metadata/num_edit_instruction_1.jsonl"
    SAVE_EDIT_METADARA_2_JSONL_PATH = "data/metadata/num_edit_instruction_2.jsonl"
    SAVE_EDIT_METADARA_3_JSONL_PATH = "data/metadata/num_edit_instruction_3.jsonl"

    # jsonlの読み込み
    with (
        open(ALL_EDIT_METADATA_JSONL_PATH, "r") as f,
        open(SAVE_EDIT_METADARA_1_JSONL_PATH, "a") as f_save_1,
        open(SAVE_EDIT_METADARA_2_JSONL_PATH, "a") as f_save_2,
        open(SAVE_EDIT_METADARA_3_JSONL_PATH, "a") as f_save_3,
    ):
        for line in f:
            json_dict = json.loads(line)

            num_edit_instruction = json_dict["num_edit_instruction"]
            
            if num_edit_instruction == "1":
                json.dump(json_dict, f_save_1, ensure_ascii=False)
                f_save_1.write("\n")
            elif num_edit_instruction == "2":
                json.dump(json_dict, f_save_2, ensure_ascii=False)
                f_save_2.write("\n")
            else:
                json.dump(json_dict, f_save_3, ensure_ascii=False)
                f_save_3.write("\n")


if __name__ == "__main__":
    main()
