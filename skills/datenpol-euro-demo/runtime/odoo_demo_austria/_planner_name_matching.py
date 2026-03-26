from __future__ import annotations

from collections import deque


def candidate_names(*names: str | None) -> tuple[str, ...]:
    values: list[str] = []
    for name in names:
        for variant in name_variants(name):
            if variant not in values:
                values.append(variant)
    return tuple(values)


def name_variants(name: str | None) -> tuple[str, ...]:
    if not name:
        return ()

    variants: list[str] = []
    pending: deque[str] = deque([name])
    seen: set[str] = set()
    replacements = (
        ("ae", "ä"),
        ("oe", "ö"),
        ("ue", "ü"),
        ("ss", "ß"),
        ("Ae", "Ä"),
        ("Oe", "Ö"),
        ("Ue", "Ü"),
        ("ä", "ae"),
        ("ö", "oe"),
        ("ü", "ue"),
        ("Ä", "Ae"),
        ("Ö", "Oe"),
        ("Ü", "Ue"),
        ("ß", "ss"),
    )

    while pending:
        current = pending.popleft()
        if current in seen:
            continue
        seen.add(current)
        variants.append(current)
        for old, new in replacements:
            if old in current:
                pending.append(current.replace(old, new))

    return tuple(variants)
