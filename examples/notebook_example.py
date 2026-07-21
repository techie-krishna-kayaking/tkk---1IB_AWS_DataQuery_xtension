# %%
# Notebook-style example for VS Code Python/Jupyter extension.
# Open this file and run cells, or copy to a real .ipynb notebook.

import os
import socket

import pandas as pd

from src.config import (
    get_aws_sso_login_cmd,
    get_aws_ssm_commands,
    get_redshift_config,
    get_selected_redshift_env,
    list_configured_redshift_envs,
)
from src.redshift_client import run_redshift_query

print("Default Redshift env:", get_selected_redshift_env())
print("Run manually in terminal for login:")
print(get_aws_sso_login_cmd())
print("\nStored SSM commands (run manually in terminal):")
for env_key, cmd in get_aws_ssm_commands().items():
    print(f"- {env_key}: {cmd}")


def _port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def _normalize_env_name(env_name: str) -> str:
    return env_name.strip().upper().replace("-", "_")


def detect_active_tunnel_envs(env_names: list[str]) -> list[str]:
    active = []
    for env in env_names:
        try:
            cfg = get_redshift_config(env)
        except Exception:
            continue
        host = str(cfg.get("host", "")).strip()
        port = int(cfg.get("port", 0))
        if host in {"localhost", "127.0.0.1"} and port > 0 and _port_open(host, port):
            active.append(env)
    return active


configured_envs = list_configured_redshift_envs()
default_env = get_selected_redshift_env()
active_tunnel_envs = detect_active_tunnel_envs(configured_envs)

# Options:
# - "auto" -> use detected tunnel env(s), else fallback to default env from .env
# - "all" -> run on all configured envs
# - "data_analyst_preprod" -> run on one env
# - ["data_analyst_dev", "data_analyst_preprod"] -> run on multiple envs
target_envs = "auto"

if target_envs == "auto":
    selected_envs = active_tunnel_envs if active_tunnel_envs else [default_env]
elif target_envs == "all":
    selected_envs = configured_envs
elif isinstance(target_envs, str):
    selected_envs = [target_envs]
else:
    selected_envs = list(target_envs)

# Some clusters do not have public schema. Override preprod schema for this session.
session_schema_overrides = {
    "data_analyst_preprod": "edw_asis",
}
for env in selected_envs:
    schema = session_schema_overrides.get(env)
    if not schema:
        continue
    normalized = _normalize_env_name(env)
    os.environ[f"REDSHIFT_SCHEMA_{normalized}"] = schema
    os.environ[f"{normalized}_SCHEMA"] = schema

print("\nConfigured envs     :", configured_envs)
print("Active tunnel envs  :", active_tunnel_envs)
print("Default env in .env :", default_env)
print("Selected env(s)     :", selected_envs)

# %%
# Connection test
test_sql = "select current_user as user_name, current_database() as db_name, current_date as run_date"
status_rows = []
for env in selected_envs:
    cfg = get_redshift_config(env)
    print("\n---", env, "---")
    print("Host / Port  :", f"{cfg['host']}:{cfg['port']}")
    print("Database/User:", f"{cfg['database']} / {cfg['user']}")
    print("Password set :", bool(cfg.get("password")))
    try:
        _ = run_redshift_query(test_sql, env_name=env)
        print("Connection test: SUCCESS")
        status_rows.append({"env": env, "status": "SUCCESS", "error": ""})
    except Exception as exc:
        print("Connection test: FAILED")
        print(type(exc).__name__, str(exc))
        status_rows.append({"env": env, "status": "FAILED", "error": f"{type(exc).__name__}: {exc}"})

pd.DataFrame(status_rows)

# %%
# Main Redshift query (single or multi-env)
redshift_sql = "select current_date as run_date"

if len(selected_envs) == 1:
    df_redshift = run_redshift_query(redshift_sql, env_name=selected_envs[0])
else:
    frames = []
    errors = []
    for env in selected_envs:
        try:
            df_env = run_redshift_query(redshift_sql, env_name=env).copy()
            df_env.insert(0, "_env", env)
            frames.append(df_env)
        except Exception as exc:
            errors.append(f"{env}: {type(exc).__name__}: {exc}")

    if frames:
        df_redshift = pd.concat(frames, ignore_index=True)
    else:
        raise RuntimeError("Query failed for all selected envs. Errors: " + " | ".join(errors))

df_redshift

# %%
from src.s3_client import read_s3_file

# Replace with your real path.
# df_s3 = read_s3_file("s3://your-bucket/path/file.parquet", limit=20)
# df_s3

# %%
from src.s3_client import query_s3_path

# Replace with your real path and optional SQL.
# df_s3_sql = query_s3_path(
#     "s3://your-bucket/path/file.parquet",
#     sql="select * from read_parquet('s3://your-bucket/path/file.parquet') limit 20"
# )
# df_s3_sql
