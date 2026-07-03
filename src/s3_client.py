from __future__ import annotations

from io import BytesIO
from pathlib import Path

import boto3
import pandas as pd

from src.config import get_s3_defaults


def list_buckets() -> list[str]:
    client = _get_s3_client()
    response = client.list_buckets()
    buckets = response.get("Buckets", [])
    return [item["Name"] for item in buckets if "Name" in item]


def list_s3_objects(bucket: str, prefix: str = "") -> list[dict[str, object]]:
    client = _get_s3_client()
    response = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    items = response.get("Contents", [])

    results: list[dict[str, object]] = []
    for item in items:
        results.append(
            {
                "key": item.get("Key", ""),
                "size": int(item.get("Size", 0)),
                "last_modified": str(item.get("LastModified", "")),
            }
        )
    return results


def read_s3_file(path: str, limit: int = 100) -> pd.DataFrame:
    bucket, key = _parse_s3_path(path)
    fmt = _infer_format(key)

    client = _get_s3_client()
    response = client.get_object(Bucket=bucket, Key=key)
    content = response["Body"].read()

    if fmt == "csv":
        return pd.read_csv(BytesIO(content)).head(limit)

    if fmt == "json":
        try:
            return pd.read_json(BytesIO(content)).head(limit)
        except ValueError:
            return pd.read_json(BytesIO(content), lines=True).head(limit)

    if fmt == "parquet":
        return pd.read_parquet(BytesIO(content)).head(limit)

    raise ValueError(f"Unsupported file type for path: {path}. Use CSV, JSON, or Parquet.")


def query_s3_path(path: str, sql: str | None = None, limit: int = 100) -> pd.DataFrame:
    try:
        import duckdb
    except ModuleNotFoundError as exc:
        raise RuntimeError("duckdb is required for query_s3_path. Run: pip install -r requirements.txt") from exc

    fmt = _infer_format(path)
    read_expr = _duckdb_reader_expr(path, fmt)

    con = duckdb.connect(database=":memory:")
    try:
        _configure_duckdb_for_s3(con)

        if sql and sql.strip():
            query = sql.strip()
        else:
            query = f"SELECT * FROM {read_expr} LIMIT {max(1, limit)}"

        return con.execute(query).fetch_df()
    finally:
        con.close()


def _get_s3_client():
    defaults = get_s3_defaults()
    profile = defaults["aws_profile"]
    region = defaults["aws_region"]

    if profile:
        session = boto3.Session(profile_name=profile, region_name=region)
    else:
        session = boto3.Session(region_name=region)

    return session.client("s3")


def _parse_s3_path(path: str) -> tuple[str, str]:
    text = path.strip()
    if not text.startswith("s3://"):
        raise ValueError(f"Invalid S3 path: {path}. Must start with s3://")

    rest = text[5:]
    parts = rest.split("/", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(f"Invalid S3 path: {path}. Expected s3://bucket/key")

    return parts[0], parts[1]


def _infer_format(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix == ".json":
        return "json"
    if suffix == ".parquet":
        return "parquet"
    return "unknown"


def _duckdb_reader_expr(path: str, fmt: str) -> str:
    escaped = path.replace("'", "''")

    if fmt == "csv":
        return f"read_csv_auto('{escaped}')"
    if fmt == "json":
        return f"read_json_auto('{escaped}')"
    if fmt == "parquet":
        return f"read_parquet('{escaped}')"

    raise ValueError(f"Unsupported S3 file type for DuckDB query: {path}")


def _configure_duckdb_for_s3(con) -> None:
    defaults = get_s3_defaults()

    con.execute("INSTALL httpfs")
    con.execute("LOAD httpfs")
    con.execute(f"SET s3_region='{defaults['aws_region']}'")

    profile = defaults["aws_profile"]
    if profile:
        session = boto3.Session(profile_name=profile, region_name=defaults["aws_region"])
    else:
        session = boto3.Session(region_name=defaults["aws_region"])

    creds = session.get_credentials()
    if creds is None:
        return

    frozen = creds.get_frozen_credentials()
    con.execute(f"SET s3_access_key_id='{frozen.access_key}'")
    con.execute(f"SET s3_secret_access_key='{frozen.secret_key}'")
    if frozen.token:
        con.execute(f"SET s3_session_token='{frozen.token}'")
