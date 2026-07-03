#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.s3_client import query_s3_path, read_s3_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview or query an S3 file path")
    parser.add_argument("--path", required=True, help="S3 path (e.g. s3://bucket/path/file.parquet)")
    parser.add_argument("--sql", default=None, help="Optional DuckDB SQL query")
    parser.add_argument("--limit", type=int, default=100, help="Default row limit when SQL is not provided")
    parser.add_argument("--csv", default=None, help="Optional output CSV file path")
    parser.add_argument("--preview", action="store_true", help="Use direct preview reader instead of DuckDB")
    args = parser.parse_args()

    try:
        if args.preview:
            df = read_s3_file(args.path, limit=max(1, args.limit))
        else:
            df = query_s3_path(args.path, sql=args.sql, limit=max(1, args.limit))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.csv:
        df.to_csv(args.csv, index=False)
        print(f"Saved {len(df)} rows to {args.csv}")

    if df.empty:
        print("No rows returned.")
        return 0

    print(df.head(max(1, args.limit)).to_string(index=False))
    print(f"\nRows returned: {len(df)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
