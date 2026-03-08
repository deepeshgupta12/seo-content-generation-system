from __future__ import annotations


def slugify(value: str) -> str:
    return (
        value.strip()
        .lower()
        .replace("/", "-")
        .replace(",", "")
        .replace(" ", "-")
    )


def compact_dict(data: dict) -> dict:
    return {k: v for k, v in data.items() if v is not None}