"""JSONのnum_edit_instructionの数字によって, それぞれ別のjsonlに保存する"""

import json
from collections import Counter

EDIT_METADARA_1_JSONL_PATH = "data/metadata/num_edit_instruction_1.jsonl"
EDIT_METADARA_2_JSONL_PATH = "data/metadata/num_edit_instruction_2.jsonl"
EDIT_METADARA_3_JSONL_PATH = "data/metadata/num_edit_instruction_3.jsonl"
SAVE_EDIT_METADARA_30_JSONL_PATH = "data/metadata/preliminary_experiment_30.jsonl"

EDIT_TYPE = {"STRUCTURE", "UPDATE", "LAYOUT", "REMOVE", "ADD"}
MAX_COUNT_PER_TYPE = 2


def main():
    counter = Counter()

    # jsonlの読み込み
    with (
        open(EDIT_METADARA_1_JSONL_PATH, "r") as f_1,
        open(EDIT_METADARA_2_JSONL_PATH, "r") as f_2,
        open(EDIT_METADARA_3_JSONL_PATH, "r") as f_3,
        open(SAVE_EDIT_METADARA_30_JSONL_PATH, "a") as f_save,
    ):
        for line in f_1:
            json_dict = json.loads(line)
            edit_type = json_dict["edit_type"]

            if counter[edit_type] >= MAX_COUNT_PER_TYPE:
                continue

            json.dump(json_dict, f_save, ensure_ascii=False)
            f_save.write("\n")
            counter[edit_type] += 1

            if all(counter[edit_type] >= MAX_COUNT_PER_TYPE for edit_type in EDIT_TYPE):
                break

        counter.clear()
        for line in f_2:
            json_dict = json.loads(line)
            edit_type = json_dict["edit_type"]

            if counter[edit_type] >= MAX_COUNT_PER_TYPE:
                continue

            json.dump(json_dict, f_save, ensure_ascii=False)
            f_save.write("\n")
            counter[edit_type] += 1

            if all(counter[edit_type] >= MAX_COUNT_PER_TYPE for edit_type in EDIT_TYPE):
                break

        counter.clear()
        for line in f_3:
            json_dict = json.loads(line)
            edit_type = json_dict["edit_type"]

            if counter[edit_type] >= MAX_COUNT_PER_TYPE:
                continue

            json.dump(json_dict, f_save, ensure_ascii=False)
            f_save.write("\n")
            counter[edit_type] += 1

            if all(counter[edit_type] >= MAX_COUNT_PER_TYPE for edit_type in EDIT_TYPE):
                break


if __name__ == "__main__":
    main()
