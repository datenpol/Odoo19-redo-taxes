from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class Json2ClientError(RuntimeError):
    """Raised when the Odoo JSON-2 API returns an error."""


class Json2Client:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        database: str | None = None,
        timeout_s: int = 30,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.database = database
        self.timeout_s = timeout_s

    @classmethod
    def from_env(
        cls,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        database: str | None = None,
        timeout_s: int = 30,
    ) -> "Json2Client":
        resolved_api_key = api_key or os.environ.get("ODOO_API_KEY")
        if not resolved_api_key:
            raise Json2ClientError("Missing API key. Set ODOO_API_KEY or pass --api-key.")
        return cls(
            base_url=base_url or os.environ.get("ODOO_BASE_URL", "https://dmdemousa.odoo19.at"),
            api_key=resolved_api_key,
            database=database or os.environ.get("ODOO_DB"),
            timeout_s=timeout_s,
        )

    def call(self, model: str, method: str, payload: dict[str, Any]) -> Any:
        url = f"{self.base_url}/json/2/{model}/{method}"
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url=url, data=body, method="POST")
        for key, value in self._headers().items():
            request.add_header(key, value)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            text = raw.decode("utf-8", errors="replace") if raw else exc.reason
            raise Json2ClientError(f"HTTP {exc.code} calling {model}.{method}: {text}") from None
        except urllib.error.URLError as exc:
            raise Json2ClientError(
                f"Transport error calling {model}.{method}: {exc.reason}"
            ) from None
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise Json2ClientError(
                f"Invalid JSON response calling {model}.{method}: {exc}"
            ) from None

    def context_get(self) -> dict[str, Any]:
        result = self.call("res.users", "context_get", {})
        if not isinstance(result, dict):
            raise Json2ClientError("res.users.context_get returned a non-object response")
        return result

    def read(
        self,
        model: str,
        ids: list[int],
        fields: list[str],
        *,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {
            "ids": ids,
            "fields": fields,
        }
        if context:
            payload["context"] = context
        result = self.call(model, "read", payload)
        if not isinstance(result, list):
            raise Json2ClientError(f"{model}.read returned a non-list response")
        return result

    def search_read(
        self,
        model: str,
        *,
        domain: list[Any],
        fields: list[str],
        order: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {
            "domain": domain,
            "fields": fields,
        }
        if order:
            payload["order"] = order
        if context:
            payload["context"] = context
        result = self.call(model, "search_read", payload)
        if not isinstance(result, list):
            raise Json2ClientError(f"{model}.search_read returned a non-list response")
        return result

    def write(
        self,
        model: str,
        ids: list[int],
        vals: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ) -> Any:
        payload: dict[str, Any] = {
            "ids": ids,
            "vals": vals,
        }
        if context:
            payload["context"] = context
        return self.call(model, "write", payload)

    def create(
        self,
        model: str,
        vals: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ) -> Any:
        payload: dict[str, Any] = {
            "vals_list": [vals],
        }
        if context:
            payload["context"] = context
        result = self.call(model, "create", payload)
        if isinstance(result, list) and len(result) == 1:
            return result[0]
        return result

    def _headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.database:
            headers["X-Odoo-Database"] = self.database
        return headers
