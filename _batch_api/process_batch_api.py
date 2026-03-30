import argparse
import logging
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

# # ログファイルを指定（1つにまとめる）
log_file = Path("_batch_api/log/batch_api.log")
log_file.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(),  # ← コンソールにも出す
    ],
)

logger = logging.getLogger(__name__)


def upload_jsonl(client: OpenAI, jsonl_path) -> Any:
    """batch api 用に生成したjsonlファイルをAPI側にupload

    Args:
        client (OpenAI): _description_
        jsonl_path: uploadするjsonlまでのパス

    Returns:
        Any: upload_file(FileObject)
    """

    with open(jsonl_path, "rb") as f:
        upload_file = client.files.create(file=f, purpose="batch")

    return upload_file


CREATE_BATCH_DESCRIPTION = "gpt-5.4にediting"


def create_batch(client: OpenAI, input_file_id: str) -> Any:
    """uploadしたjsonlを元に, リクエストの開始

    Args:
        client (OpenAI): _description_
        input_file_id (str): batch_input_file.input_file_id

    Returns:
        Any: batch(Batch オジジェクト)
    """
    batch = client.batches.create(
        input_file_id=input_file_id,
        endpoint="/v1/responses",
        completion_window="24h",
        metadata={"description": CREATE_BATCH_DESCRIPTION},
    )

    return batch


def check_status(client: OpenAI, batch_id: str) -> Any:
    """リクエストを送ったbatchのstatusをチェックする

    Args:
        client (OpenAI): _description_
        batch_id (str): batch.id

    Returns:
        Any: status_batch(BatchObject)
    """
    status_batch = client.batches.retrieve(batch_id)
    return status_batch


def retrieve_result(client: OpenAI, output_file_id: str) -> Any:
    """output_file_id を元にbatch apiの結果(jsonl)

    Args:
        client (OpenAI): _description_
        output_file_id (str): status_batch.output_file_id

    Returns:
        Any: file_response(FileObject)
    """
    file_response = client.files.content(output_file_id)
    return file_response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("upload_jsonl_path", help="uploadするjsonlへのパス")
    parser.add_argument(
        "save_jsonl_path", help="batch api側から返ってきた結果を保存するjsonlへのパス"
    )

    args = parser.parse_args()

    load_dotenv()
    client = OpenAI()

    upload_file = upload_jsonl(client, args.upload_jsonl_path)

    # デバッグ用
    logger.info(upload_file.id)

    batch = create_batch(client, upload_file.id)
    # デバッグ用
    logger.info(batch.id)

    # statusの確認
    while True:
        status_batch = check_status(client, batch.id)
        status = status_batch.status

        if status == "completed":
            # デバッグ用
            logger.info("##################")
            logger.info(status_batch)
            logger.info("API リクエスト完了")
            logger.info("##################")
            break
        elif status in ("failed", "cancelled", "expired"):
            raise RuntimeError(f"Batch failed: {status}")

        time.sleep(120)

    file_response = retrieve_result(client, status_batch.output_file_id)

    with open(args.save_jsonl_path, "w", encoding="utf-8") as f_save:
        f_save.write(file_response.text)

    logger.info("##################")
    logger.info("Batch APIの全ての処理が終了しました")
    logger.info("##################")


if __name__ == "__main__":
    main()
