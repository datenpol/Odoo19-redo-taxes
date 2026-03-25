from __future__ import annotations

import json
from dataclasses import dataclass
from enum import IntEnum
from typing import Any


class ExitCode(IntEnum):
    SUCCESS = 0
    BAD_INVOCATION = 2
    API_FAILURE = 3
    PREFLIGHT_FAILURE = 4
    APPLY_FAILURE = 5
    VALIDATION_FAILURE = 6
    INTERNAL_ERROR = 7


@dataclass(frozen=True)
class StageReport:
    status: str
    summary: str
    messages: tuple[str, ...] = ()
    operation_count: int | None = None
    issue_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "status": self.status,
            "summary": self.summary,
            "messages": list(self.messages),
        }
        if self.operation_count is not None:
            data["operation_count"] = self.operation_count
        if self.issue_count is not None:
            data["issue_count"] = self.issue_count
        return data


@dataclass(frozen=True)
class CommandReport:
    command: str
    mode: str
    base_url: str
    status: str
    summary: str
    exit_code: int
    preflight: StageReport
    apply: StageReport
    validation: StageReport

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "mode": self.mode,
            "base_url": self.base_url,
            "status": self.status,
            "summary": self.summary,
            "exit_code": self.exit_code,
            "preflight": self.preflight.to_dict(),
            "apply": self.apply.to_dict(),
            "validation": self.validation.to_dict(),
        }


def skipped_stage(summary: str = "Not run.") -> StageReport:
    return StageReport(status="skipped", summary=summary)


def emit_report(report: CommandReport, output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
        return
    print(_render_text(report))


def _render_text(report: CommandReport) -> str:
    lines = [f"[{_label(report.status)}] {report.summary}"]
    stages = (
        ("preflight", report.preflight),
        ("apply", report.apply),
        ("validation", report.validation),
    )
    for stage_name, stage in stages:
        lines.append(f"[{_label(stage.status)}] {stage_name}: {stage.summary}")
        for message in stage.messages:
            lines.append(f"- {message}")
    return "\n".join(lines)


def _label(status: str) -> str:
    return {
        "success": "OK",
        "failure": "FAIL",
        "skipped": "SKIP",
    }.get(status, status.upper())
