import json
from pathlib import Path

# JSONLファイルを読み込む
with open("_batch_api/work/result.jsonl", "r", encoding="utf-8") as f_jsonl:
    # data = json.load(f)
    for line in f_jsonl:
        data = json.loads(line)
        custom_id = data["custom_id"]

        # text部分を取り出す
        text = data["response"]["body"]["output"][0]["content"][0]["text"]

        # 改行を保持したまま保存
        save_dir = Path("work/")
        save_dir.mkdir(parents=True, exist_ok=True)
        with open(f"{save_dir}/{custom_id}.txt", "w", encoding="utf-8") as f:
            f.write(text)