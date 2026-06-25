import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests
from sqlalchemy import create_engine, text


def load_config(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def iter_rows(connection_uri: str, query: str):
    engine = create_engine(connection_uri, pool_pre_ping=True)
    with engine.connect() as connection:
        result = connection.execute(text(query))
        columns = list(result.keys())
        for row in result:
            yield dict(zip(columns, row))


def chunks(items, size: int):
    batch = []
    for item in items:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def normalize_value(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def build_records(rows: list[dict], primary_key: str) -> list[dict]:
    collected_at = datetime.now(timezone.utc).isoformat()
    records = []
    for row in rows:
        payload = {key: normalize_value(value) for key, value in row.items()}
        source_record_id = str(payload.get(primary_key) or uuid.uuid4())
        records.append(
            {
                "source_record_id": source_record_id,
                "payload": payload,
                "collected_at": collected_at,
            }
        )
    return records


def send_batch(config: dict, records: list[dict]) -> dict:
    idempotency_key = f"{config['data_source_id']}-{uuid.uuid4()}"
    response = requests.post(
        f"{config['sentinela_api_url'].rstrip('/')}/ingestion/batches",
        headers={"X-Agent-Token": config["agent_token"]},
        json={
            "data_source_id": config["data_source_id"],
            "idempotency_key": idempotency_key,
            "records": records,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def run(config_path: str) -> None:
    config = load_config(config_path)
    batch_size = int(config.get("batch_size", 500))
    rows = iter_rows(config["connection_uri"], config["query"])
    total = 0
    for row_batch in chunks(rows, batch_size):
        records = build_records(row_batch, config["primary_key"])
        result = send_batch(config, records)
        total += len(records)
        print(f"sent batch={result['id']} records={len(records)} status={result['status']}")
    print(f"done total_records={total}")


def main() -> None:
    parser = argparse.ArgumentParser(description="SENTINELA client-side data collector")
    parser.add_argument("--config", default="config.json", help="Path to collector config JSON")
    args = parser.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()
