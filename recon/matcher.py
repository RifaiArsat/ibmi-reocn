"""Duplicate classification and cross-file transaction matching."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any

from .loader import Transaction


def _amount(value: Decimal) -> str:
    return format(value, ".2f")


def _date(value: Any) -> str | None:
    return value.isoformat() if value is not None else None


def _classify(records: list[Transaction], file_label: str) -> tuple[dict[str, Transaction], list[dict[str, Any]], list[dict[str, Any]], set[str]]:
    grouped: dict[str, list[Transaction]] = defaultdict(list)
    for record in records:
        grouped[record.key].append(record)

    usable: dict[str, Transaction] = {}
    duplicates: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    conflicted: set[str] = set()

    for key in set(grouped):
        entries = grouped[key]
        usable[key] = entries[-1]
        if len(entries) > 1:
            duplicates.append({
                "file": file_label,
                "key": key,
                "amount": _amount(entries[-1].amount),
                "rows": sorted(item.row for item in entries),
            })
    return usable, duplicates, conflicts, conflicted


def reconcile(ledger: list[Transaction], bank: list[Transaction]) -> dict[str, Any]:
    """Return matching, duplicate, conflict, and missing groups."""
    ledger_by_key, ledger_dups, ledger_conflicts, ledger_bad = _classify(ledger, "ledger")
    bank_by_key, bank_dups, bank_conflicts, bank_bad = _classify(bank, "bank")
    excluded = ledger_bad | bank_bad

    matched: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []
    missing_in_bank: list[dict[str, Any]] = []
    missing_in_ledger: list[dict[str, Any]] = []

    for key in (set(ledger_by_key) | set(bank_by_key)) - excluded:
        left = ledger_by_key.get(key)
        right = bank_by_key.get(key)
        if left is not None and right is not None:
            if left.amount == right.amount:
                matched.append({
                    "key": key,
                    "amount": _amount(left.amount),
                    "ledger_date": _date(left.date),
                    "bank_date": _date(right.date),
                })
            else:
                mismatches.append({
                    "key": key,
                    "ledger_amount": _amount(left.amount),
                    "bank_amount": _amount(right.amount),
                    "delta": _amount(right.amount - left.amount),
                    "ledger_date": _date(left.date),
                    "bank_date": _date(right.date),
                })
        elif left is not None:
            missing_in_bank.append({"key": key, "amount": _amount(left.amount), "date": _date(left.date)})
        elif right is not None:
            missing_in_ledger.append({"key": key, "amount": _amount(right.amount), "date": _date(right.date)})

    sort_key = lambda item: (item.get("key", ""), item.get("row", 0), item.get("file", ""))
    return {
        "matched": matched,
        "missing_in_bank": missing_in_bank,
        "missing_in_ledger": missing_in_ledger,
        "amount_mismatches": mismatches,
        "duplicates": ledger_dups + bank_dups,
        "conflicts": sorted(ledger_conflicts + bank_conflicts, key=sort_key),
        "invalid_records": [],
    }
