import os
import socket

import pandas as pd

from src.config import get_redshift_config, get_selected_redshift_env, list_configured_redshift_envs
from src.redshift_client import run_redshift_query


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

print("Configured envs     :", configured_envs)
print("Active tunnel envs  :", active_tunnel_envs)
print("Default env in .env :", default_env)
print("Selected env(s)     :", selected_envs)

sql = "select current_date as run_date"

if len(selected_envs) == 1:
	df = run_redshift_query(sql, env_name=selected_envs[0])
else:
	frames = []
	errors = []
	for env in selected_envs:
		try:
			df_env = run_redshift_query(sql, env_name=env).copy()
			df_env.insert(0, "_env", env)
			frames.append(df_env)
		except Exception as exc:
			errors.append(f"{env}: {type(exc).__name__}: {exc}")

	if frames:
		df = pd.concat(frames, ignore_index=True)
	else:
		raise RuntimeError("Query failed for all selected envs. Errors: " + " | ".join(errors))

print(df)
