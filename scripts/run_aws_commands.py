#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml


def load_commands(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("commands"), list):
        raise ValueError("Invalid YAML format. Expected top-level 'commands' list.")

    commands: list[dict[str, str]] = []
    for item in payload["commands"]:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        command = str(item.get("command", "")).strip()
        description = str(item.get("description", "")).strip()
        if not name or not command:
            continue
        commands.append({"name": name, "description": description, "command": command})

    if not commands:
        raise ValueError("No valid commands found in YAML.")

    return commands


def run_command(command: str, dry_run: bool) -> int:
    print(f"\n$ {command}")
    if dry_run:
        return 0

    result = subprocess.run(command, shell=True)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AWS commands from YAML one-by-one")
    parser.add_argument(
        "--file",
        default="aws_commands.yaml",
        help="Path to YAML file (default: aws_commands.yaml)",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Run only one command by name",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all commands in order",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Run without per-command confirmation",
    )
    args = parser.parse_args()

    yaml_path = Path(args.file).expanduser().resolve()

    try:
        commands = load_commands(yaml_path)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.name:
        selected = [cmd for cmd in commands if cmd["name"] == args.name]
        if not selected:
            print(f"ERROR: Command name '{args.name}' not found in {yaml_path}", file=sys.stderr)
            return 1
    elif args.all:
        selected = commands
    else:
        print("Available commands:")
        for cmd in commands:
            desc = f" - {cmd['description']}" if cmd["description"] else ""
            print(f"  {cmd['name']}{desc}")
        print("\nUse --name <command_name> to run one command, or --all to run all in order.")
        return 0

    for idx, cmd in enumerate(selected, start=1):
        print(f"\n[{idx}/{len(selected)}] {cmd['name']}")
        if cmd["description"]:
            print(f"Description: {cmd['description']}")

        if not args.yes:
            answer = input("Run this command? [y/N]: ").strip().lower()
            if answer not in {"y", "yes"}:
                print("Skipped.")
                continue

        exit_code = run_command(cmd["command"], dry_run=args.dry_run)
        if exit_code != 0:
            print(f"Command failed with exit code {exit_code}. Stopping.", file=sys.stderr)
            return exit_code

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
