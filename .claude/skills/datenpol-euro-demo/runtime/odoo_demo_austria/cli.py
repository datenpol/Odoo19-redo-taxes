from __future__ import annotations

import argparse
import os
from pathlib import Path

from ._cli_contract import emit_report
from ._cli_runtime import execute_command, resolved_base_url, unexpected_report
from .json2_client import Json2Client, Json2ClientError
from .spec_loader import load_spec


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return _system_exit_code(exc)

    try:
        spec = load_spec(args.spec)
        client = _build_client(parser, args)
    except SystemExit as exc:
        return _system_exit_code(exc)
    except Exception as exc:
        report = unexpected_report(
            command=args.command,
            base_url=resolved_base_url(args.base_url),
            summary=f"Failed to initialize the engine: {exc}",
        )
        emit_report(report, args.output_format)
        return report.exit_code

    report = execute_command(args.command, client, spec)
    emit_report(report, args.output_format)
    return report.exit_code


def _build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--spec",
        default=str(Path("data") / "austria-cosmetic-mapping-spec.draft.yaml"),
        help="Path to the translation-aware mapping spec.",
    )
    common.add_argument(
        "--base-url",
        default=None,
        help="Instance root URL, for example https://codexplayground.odoo19.at",
    )
    common.add_argument(
        "--database",
        default=None,
        help="Optional X-Odoo-Database header value.",
    )
    common.add_argument(
        "--api-key",
        default=None,
        help="API key. Prefer the environment variable instead of passing it directly.",
    )
    common.add_argument(
        "--api-key-env",
        default="ODOO_API_KEY",
        help="Environment variable name that contains the API key.",
    )
    common.add_argument(
        "--timeout-s",
        type=int,
        default=30,
        help="HTTP timeout in seconds.",
    )
    common.add_argument(
        "--format",
        dest="output_format",
        default="text",
        choices=("text", "json"),
        help="Output format for operators and wrappers.",
    )

    parser = argparse.ArgumentParser(description="Odoo 19 demo Austria patcher", parents=[common])

    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("doctor", "apply", "validate", "run"):
        subparsers.add_parser(command, parents=[common])

    return parser


def _resolve_api_key(explicit_api_key: str | None, api_key_env: str) -> str | None:
    return explicit_api_key or os.environ.get(api_key_env)


def _build_client(parser: argparse.ArgumentParser, args: argparse.Namespace) -> Json2Client:
    try:
        return Json2Client.from_env(
            base_url=args.base_url,
            api_key=_resolve_api_key(args.api_key, args.api_key_env),
            database=args.database,
            timeout_s=args.timeout_s,
        )
    except Json2ClientError as exc:
        parser.error(str(exc))


def _system_exit_code(exc: SystemExit) -> int:
    if exc.code is None:
        return 0
    if isinstance(exc.code, int):
        return exc.code
    return 1
