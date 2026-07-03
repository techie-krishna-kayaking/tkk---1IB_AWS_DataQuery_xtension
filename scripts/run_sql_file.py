#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.redshift_client import run_redshift_sql_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SQL from a .sql file against Redshift")
    parser.add_argument("--env", default=None, help="Redshift environment name (e.g. data_analyst_dev)")
    parser.add_argument("--file", required=True, help="Path to .sql file")
    parser.add_argument("--csv", default=None, help="Optional output CSV file path")
    parser.add_argument("--limit", type=int, default=50, help="Rows to print to terminal")
    args = parser.parse_args()

    try:
        df = run_redshift_sql_file(args.file, env_name=args.env)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.csv:
        df.to_csv(args.csv, index=False)
        print(f"Saved {len(df)} rows to {args.csv}")

    if df.empty:
        print("SQL executed. No rows returned.")
        return 0

    print(df.head(max(1, args.limit)).to_string(index=False))
    print(f"\nRows returned: {len(df)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
