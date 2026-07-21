from __future__ import annotations

from pathlib import Path

import pandas as pd
import redshift_connector

from src.config import get_redshift_config


def get_redshift_connection(env_name: str | None = None):
    cfg = get_redshift_config(env_name)
    return redshift_connector.connect(
        host=cfg["host"],
        port=cfg["port"],
        database=cfg["database"],
        user=cfg["user"],
        password=cfg["password"],
    )


def run_redshift_query(sql: str, env_name: str | None = None) -> pd.DataFrame:
    sql_text = sql.strip()
    if not sql_text:
        raise ValueError("SQL text is empty")

    cfg = get_redshift_config(env_name)
    conn = get_redshift_connection(cfg["env"])
    try:
        with conn.cursor() as cursor:
            if cfg["schema"]:
                try:
                    cursor.execute(f"SET search_path TO {cfg['schema']}")
                except Exception as exc:
                    msg = str(exc).lower()
                    # Some environments do not have a public/default schema.
                    # In that case continue without overriding search_path.
                    if "schema" in msg and "does not exist" in msg:
                        pass
                    else:
                        raise

            cursor.execute(sql_text)

            if not cursor.description:
                return pd.DataFrame()

            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            return pd.DataFrame(rows, columns=columns)
    finally:
        conn.close()


def run_redshift_sql_file(sql_file_path: str, env_name: str | None = None) -> pd.DataFrame:
    path = Path(sql_file_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")

    sql_text = path.read_text(encoding="utf-8")
    return run_redshift_query(sql_text, env_name=env_name)
