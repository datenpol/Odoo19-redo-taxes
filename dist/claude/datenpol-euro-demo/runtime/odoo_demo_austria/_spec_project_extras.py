from __future__ import annotations

from typing import Any

from ._spec_support import (
    optional_int,
    optional_str,
    parse_translated_text,
    require_bool,
    require_int,
    require_list,
    require_mapping,
    require_str,
)
from .models import AccountSpec, ChartSpec, ValidationSpec


def parse_chart(root: dict[str, Any]) -> ChartSpec:
    chart = require_mapping(root.get("chart"), "chart")
    return ChartSpec(
        strategy=require_str(chart.get("strategy"), "chart.strategy"),
        reason=require_str(chart.get("reason"), "chart.reason"),
        name_precedence=tuple(
            require_str(item, "chart.name_precedence[]")
            for item in require_list(chart.get("name_precedence"), "chart.name_precedence")
        ),
        core_reference_accounts=parse_core_reference_accounts(chart),
        explicit_accounts=parse_accounts(chart),
    )


def parse_core_reference_accounts(chart: dict[str, Any]) -> dict[str, int]:
    accounts = require_mapping(
        chart.get("core_reference_accounts"),
        "chart.core_reference_accounts",
    )
    return {
        require_str(key, "chart.core_reference_accounts.key"): require_int(
            value,
            f"chart.core_reference_accounts[{key}]",
        )
        for key, value in accounts.items()
    }


def parse_accounts(chart: dict[str, Any]) -> tuple[AccountSpec, ...]:
    accounts: list[AccountSpec] = []
    for index, entry in enumerate(
        require_list(chart.get("explicit_accounts"), "chart.explicit_accounts")
    ):
        item = require_mapping(entry, f"chart.explicit_accounts[{index}]")
        accounts.append(
            AccountSpec(
                record_id=require_int(
                    item.get("id"),
                    f"chart.explicit_accounts[{index}].id",
                ),
                create_if_missing=require_bool(
                    item.get("create_if_missing", False),
                    f"chart.explicit_accounts[{index}].create_if_missing",
                ),
                optional=require_bool(
                    item.get("optional", False),
                    f"chart.explicit_accounts[{index}].optional",
                ),
                code=require_str(
                    item.get("code"),
                    f"chart.explicit_accounts[{index}].code",
                ),
                source_name=optional_str(
                    item.get("source_name"),
                    f"chart.explicit_accounts[{index}].source_name",
                ),
                target_name=parse_translated_text(
                    item.get("target_name"),
                    f"chart.explicit_accounts[{index}].target_name",
                ),
                posted_lines=require_int(
                    item.get("posted_lines"),
                    f"chart.explicit_accounts[{index}].posted_lines",
                ),
                account_type=optional_str(
                    item.get("account_type"),
                    f"chart.explicit_accounts[{index}].account_type",
                ),
                reconcile=require_bool(
                    item.get("reconcile", False),
                    f"chart.explicit_accounts[{index}].reconcile",
                ),
                reference_account_id=optional_int(
                    item.get("reference_account_id"),
                    f"chart.explicit_accounts[{index}].reference_account_id",
                ),
            )
        )
    return tuple(accounts)


def parse_validation(root: dict[str, Any]) -> ValidationSpec:
    validation = require_mapping(root.get("validation"), "validation")
    return ValidationSpec(
        api_assertions=tuple(
            require_str(item, "validation.api_assertions[]")
            for item in require_list(
                validation.get("api_assertions"),
                "validation.api_assertions",
            )
        ),
        ui_spot_checks=tuple(
            require_str(item, "validation.ui_spot_checks[]")
            for item in require_list(
                validation.get("ui_spot_checks"),
                "validation.ui_spot_checks",
            )
        ),
    )
