#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

DEFAULT_BASE_URL = "https://dmdemousa.odoo19.at"


def _eprint(*parts: object) -> None:
    print(*parts, file=sys.stderr)


def _normalize_base_url(base_url: str) -> str:
    return base_url.strip().rstrip("/")


def _headers(api_key: str, database: str | None) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if database:
        headers["X-Odoo-Database"] = database
    return headers


def _http_json(
    *,
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    body: Any | None = None,
    timeout_s: int = 30,
) -> Any:
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url=url, data=data, method=method)
    for k, v in (headers or {}).items():
        request.add_header(k, v)

    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            raw = response.read()
            if not raw:
                return None
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        text = raw.decode("utf-8", errors="replace") if raw else ""
        try:
            parsed = json.loads(text) if text else None
        except json.JSONDecodeError:
            parsed = None

        if parsed is not None:
            raise RuntimeError(
                f"HTTP {exc.code} calling {url}: {json.dumps(parsed, ensure_ascii=False)}"
            ) from None
        raise RuntimeError(f"HTTP {exc.code} calling {url}: {text or exc.reason}") from None


def cmd_version(args: argparse.Namespace) -> int:
    base_url = _normalize_base_url(args.base_url)
    url = f"{base_url}/web/version"
    result = _http_json(method="GET", url=url, timeout_s=args.timeout_s)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _require_api_key(args: argparse.Namespace) -> str:
    api_key = args.api_key or os.environ.get("ODOO_API_KEY")
    if not api_key:
        _eprint("Missing API key. Set ODOO_API_KEY or pass --api-key.")
        return ""
    return api_key


def cmd_context(args: argparse.Namespace) -> int:
    api_key = _require_api_key(args)
    if not api_key:
        return 2

    base_url = _normalize_base_url(args.base_url)
    url = f"{base_url}/json/2/res.users/context_get"
    result = _http_json(
        method="POST",
        url=url,
        headers=_headers(api_key, args.database),
        body={},
        timeout_s=args.timeout_s,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cmd_call(args: argparse.Namespace) -> int:
    api_key = _require_api_key(args)
    if not api_key:
        return 2

    base_url = _normalize_base_url(args.base_url)
    url = f"{base_url}/json/2/{args.model}/{args.method}"

    try:
        payload = json.loads(args.data)
    except json.JSONDecodeError as exc:
        _eprint(f"Invalid JSON for --data: {exc}")
        return 2

    result = _http_json(
        method="POST",
        url=url,
        headers=_headers(api_key, args.database),
        body=payload,
        timeout_s=args.timeout_s,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Quick JSON-2 client for an Odoo 19 demo instance."
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("ODOO_BASE_URL", DEFAULT_BASE_URL),
        help="Instance root URL (e.g. https://example.com).",
    )
    parser.add_argument(
        "--database",
        default=os.environ.get("ODOO_DB"),
        help="Optional DB name header (X-Odoo-Database).",
    )
    parser.add_argument(
        "--timeout-s",
        type=int,
        default=30,
        help="HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="API key (prefer ODOO_API_KEY env var; this flag is visible in shell history).",
    )

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ver = sub.add_parser("version", help="Fetch /web/version (no auth).")
    p_ver.set_defaults(func=cmd_version)

    p_ctx = sub.add_parser("context", help="Fetch res.users/context_get (auth check).")
    p_ctx.set_defaults(func=cmd_context)

    p_call = sub.add_parser(
        "call", help="Call any /json/2/<model>/<method> with custom JSON payload."
    )
    p_call.add_argument("model", help="Model name (e.g. res.partner).")
    p_call.add_argument("method", help="Method name (e.g. search_read).")
    p_call.add_argument(
        "--data",
        default="{}",
        help="JSON payload to send (positional args list or named-args object).",
    )
    p_call.set_defaults(func=cmd_call)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
