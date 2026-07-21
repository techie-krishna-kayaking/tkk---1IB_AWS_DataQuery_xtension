#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import get_aws_sso_login_cmd, get_aws_ssm_command, get_aws_ssm_commands, get_selected_redshift_env


def _run_command(command: str, label: str) -> int:
    print(f"\n[{label}]\n$ {command}")
    result = subprocess.run(command, shell=True)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Single command to login (SSO) and open Redshift SSM tunnel"
    )
    parser.add_argument(
        "--env",
        default=None,
        help="Environment name (e.g. data_analyst_dev, data_qa_dev, data_analyst_preprod)",
    )
    parser.add_argument(
        "--skip-sso",
        action="store_true",
        help="Skip AWS SSO login and only start the SSM tunnel",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available SSM tunnel environments and exit",
    )
    args = parser.parse_args()

    available = get_aws_ssm_commands()
    if args.list:
        if not available:
            print("No AWS_SSM_CMD_<ENV> commands found in .env")
            return 1
        print("Available environments:")
        for env_key in sorted(available):
            print(f"- {env_key}")
        return 0

    try:
        selected_env = args.env.strip() if args.env else get_selected_redshift_env()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    ssm_cmd = get_aws_ssm_command(selected_env)
    if not ssm_cmd:
        print(f"ERROR: No SSM command configured for env '{selected_env}'", file=sys.stderr)
        if available:
            print("Available environments:", file=sys.stderr)
            for env_key in sorted(available):
                print(f"- {env_key}", file=sys.stderr)
        return 1

    if not args.skip_sso:
        sso_cmd = get_aws_sso_login_cmd()
        sso_exit = _run_command(sso_cmd, "AWS SSO login")
        if sso_exit != 0:
            print(f"SSO login failed with exit code {sso_exit}", file=sys.stderr)
            return sso_exit

    print(f"\nSelected Redshift env: {selected_env}")
    print("Starting SSM tunnel. Keep this terminal open while querying from notebook.")
    return _run_command(ssm_cmd, "SSM tunnel")


if __name__ == "__main__":
    raise SystemExit(main())
