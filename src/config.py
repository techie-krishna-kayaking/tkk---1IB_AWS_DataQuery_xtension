from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from dotenv import find_dotenv, load_dotenv


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


def load_env(dotenv_path: str | None = None) -> None:
    if dotenv_path:
        path = Path(dotenv_path).expanduser()
        if not path.exists():
            raise ConfigError(f".env file not found at {path}")
        load_dotenv(path, override=False)
        return

    discovered = find_dotenv(usecwd=True)
    if discovered:
        load_dotenv(discovered, override=False)


def _normalize_env_name(env_name: str) -> str:
    return env_name.strip().upper().replace("-", "_")


def _get_required(key: str) -> str:
    value = os.getenv(key, "").strip()
    if not value:
        raise ConfigError(f"Missing required environment variable: {key}")
    return value


def _get_int(key: str, default: int | None = None) -> int:
    raw = os.getenv(key, "").strip()
    if not raw:
        if default is None:
            raise ConfigError(f"Missing required integer environment variable: {key}")
        return default

    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"Environment variable {key} must be an integer, got: {raw}") from exc


def _candidate_prefixes(normalized_env: str) -> list[str]:
    # Support aliases like DATA_ANALYST_PREPROD -> PREPROD for JDBC-style keys.
    parts = [p for p in normalized_env.split("_") if p]
    if not parts:
        return [normalized_env]

    prefixes = [normalized_env]
    for i in range(1, len(parts)):
        prefixes.append("_".join(parts[i:]))
    return prefixes


def _parse_jdbc_url(jdbc_url: str) -> dict[str, Any]:
    # Format: jdbc:redshift://host:port/database
    pattern = r"^jdbc:redshift://([^:/]+):(\d+)/(.+)$"
    match = re.match(pattern, jdbc_url.strip(), flags=re.IGNORECASE)
    if not match:
        raise ConfigError(f"Invalid JDBC URL format: {jdbc_url}")

    host, port_raw, database = match.groups()
    try:
        port = int(port_raw)
    except ValueError as exc:
        raise ConfigError(f"Invalid port in JDBC URL: {jdbc_url}") from exc

    return {
        "host": host,
        "port": port,
        "database": database,
    }


def list_configured_redshift_envs() -> list[str]:
    names: set[str] = set()
    redshift_prefix = "REDSHIFT_HOST_"
    jdbc_suffix = "_JDBC_URL"

    for key in os.environ:
        if key.startswith(redshift_prefix):
            names.add(key[len(redshift_prefix):].lower())
        elif key.endswith(jdbc_suffix):
            names.add(key[: -len(jdbc_suffix)].lower())

    return sorted(names)


def get_selected_redshift_env() -> str:
    selected = os.getenv("REDSHIFT_ENV", "").strip()
    if selected:
        return selected

    candidates = list_configured_redshift_envs()
    if candidates:
        return candidates[0]

    raise ConfigError(
        "No REDSHIFT_ENV selected and no REDSHIFT_HOST_<ENV> or <ENV>_JDBC_URL variables found in .env"
    )


def get_redshift_config(env_name: str | None = None) -> dict[str, Any]:
    selected = env_name.strip() if env_name else get_selected_redshift_env()
    normalized = _normalize_env_name(selected)

    # Preferred format (existing): REDSHIFT_HOST_<ENV>, REDSHIFT_PORT_<ENV>, ...
    host_key = f"REDSHIFT_HOST_{normalized}"
    if os.getenv(host_key, "").strip():
        host = _get_required(host_key)
        port = _get_int(f"REDSHIFT_PORT_{normalized}")
        database = _get_required(f"REDSHIFT_DB_{normalized}")
        user = _get_required(f"REDSHIFT_USER_{normalized}")
        password = os.getenv(f"REDSHIFT_PASSWORD_{normalized}", "")
        schema = os.getenv(f"REDSHIFT_SCHEMA_{normalized}", "public").strip() or "public"

        return {
            "env": selected,
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
            "schema": schema,
        }

    # Compatibility format: <ENV>_JDBC_URL, <ENV>_USER, <ENV>_PASSWORD, <ENV>_SCHEMA
    matched_prefix = ""
    jdbc_url = ""
    for prefix in _candidate_prefixes(normalized):
        key = f"{prefix}_JDBC_URL"
        value = os.getenv(key, "").strip()
        if value:
            matched_prefix = prefix
            jdbc_url = value
            break

    if not jdbc_url:
        raise ConfigError(
            f"Missing configuration for env '{selected}'. Expected either "
            f"REDSHIFT_HOST_{normalized} or one of {', '.join(f'{p}_JDBC_URL' for p in _candidate_prefixes(normalized))}"
        )

    jdbc = _parse_jdbc_url(jdbc_url)
    user = _get_required(f"{matched_prefix}_USER")
    password = os.getenv(f"{matched_prefix}_PASSWORD", "")
    schema = os.getenv(f"{matched_prefix}_SCHEMA", "public").strip() or "public"

    return {
        "env": selected,
        "host": jdbc["host"],
        "port": jdbc["port"],
        "database": jdbc["database"],
        "user": user,
        "password": password,
        "schema": schema,
    }


def get_aws_sso_login_cmd() -> str:
    return os.getenv("AWS_SSO_LOGIN_CMD", "aws sso login --sso-session infoblox").strip()


def get_aws_ssm_commands() -> dict[str, str]:
    result: dict[str, str] = {}
    prefix = "AWS_SSM_CMD_"
    for key, value in os.environ.items():
        if key.startswith(prefix) and value.strip():
            env_key = key[len(prefix):].lower()
            result[env_key] = value.strip()
    return result


def get_aws_ssm_command(env_name: str) -> str | None:
    normalized = _normalize_env_name(env_name)
    return os.getenv(f"AWS_SSM_CMD_{normalized}")


def get_s3_defaults() -> dict[str, Any]:
    return {
        "aws_region": os.getenv("AWS_REGION", "us-east-1").strip(),
        "aws_profile": os.getenv("AWS_PROFILE", "").strip(),
        "default_bucket": os.getenv("S3_DEFAULT_BUCKET", "").strip(),
        "default_prefix": os.getenv("S3_DEFAULT_PREFIX", "").strip(),
        "default_row_limit": _get_int("DEFAULT_ROW_LIMIT", default=100),
    }


load_env()
