"""CSV loading and row validation."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from .normalize import normalize_key, parse_amount, parse_ibmi_date


REQUIRED_COLUMNS = ("txn_id", "amount", "date")


@dataclass(frozen=True)
class Transaction:
    key: str
    amount: Decimal
    date: date | None
    row: int


@dataclass(frozen=True)
class InvalidRecord:
    file: str
    row: int
    reason: str
    key: str


def load_csv(path: str | Path, file_label: str) -> tuple[list[Transaction], list[InvalidRecord]]:
    """Load records, applying validation precedence key, amount, then date."""
    records: list[Transaction] = []
    invalid: list[InvalidRecord] = []

    with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None or not set(REQUIRED_COLUMNS).issubset(reader.fieldnames):
            raise ValueError(f"{path}: CSV must contain columns {', '.join(REQUIRED_COLUMNS)}")

        for row_number, row in enumerate(reader, start=1):
            try:
                if None in row:
                    raise ValueError("malformed row")
                raw_key = row.get("txn_id") or ""
                key = normalize_key(raw_key) if file_label == "ledger" else raw_key
                if not key:
                    invalid.append(InvalidRecord(file_label, row_number, "key", key))
                    continue
                try:
                    amount = parse_amount(row.get("amount"))
                except ValueError:
                    invalid.append(InvalidRecord(file_label, row_number, "amount", key))
                    continue
                try:
                    txn_date = parse_ibmi_date(row.get("date"))
                except ValueError:
                    invalid.append(InvalidRecord(file_label, row_number, "date", key))
                    continue
                records.append(Transaction(key, amount, txn_date, row_number))
            except Exception:
                continue

    return records, invalid
