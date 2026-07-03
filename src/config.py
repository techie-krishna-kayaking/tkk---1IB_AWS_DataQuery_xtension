from __future__ import annotations

import os
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


def list_configured_redshift_envs() -> list[str]:
    suffix = "REDSHIFT_HOST_"
    names: list[str] = []
    for key in os.environ:
        if key.startswith(suffix):
            names.append(key[len(suffix):].lower())
    return sorted(names)


def get_selected_redshift_env() -> str:
    selected = os.getenv("REDSHIFT_ENV", "").strip()
    if selected:
        return selected

    candidates = list_configured_redshift_envs()
    if candidates:
        return candidates[0]

    raise ConfigError(
        "No REDSHIFT_ENV selected and no REDSHIFT_HOST_<ENV> variables found in .env"
    )


def get_redshift_config(env_name: str | None = None) -> dict[str, Any]:
    selected = env_name.strip() if env_name else get_selected_redshift_env()
    normalized = _normalize_env_name(selected)

    host = _get_required(f"REDSHIFT_HOST_{normalized}")
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
