"""Input normalization and IBM i date decoding."""

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


CENT = Decimal("0.01")


def normalize_key(value: str | None) -> str:
    """Trim surrounding whitespace and uppercase a transaction key."""
    return (value or "").strip().upper()


def parse_amount(value: str | None) -> Decimal:
    """Parse a finite amount and round it to cents."""
    if value is None:
        raise ValueError("amount")
    try:
        amount = Decimal(float(value.strip()))
        if not amount.is_finite():
            raise ValueError("amount")
        return amount.quantize(CENT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("amount") from exc


def parse_ibmi_date(value: str | None) -> date | None:
    """Decode a seven-digit CYYMMDD IBM i date; all zeroes means no date."""
    if value is None:
        raise ValueError("date")
    raw = value.strip()
    if len(raw) != 7 or not raw.isascii() or not raw.isdigit():
        raise ValueError("date")
    if raw == "0000000":
        return None

    century_digit = raw[0]
    if century_digit not in ("0", "1"):
        raise ValueError("date")
    year = (1900 if century_digit == "0" else 2000) + int(raw[1:3])
    month = int(raw[3:5])
    day = int(raw[5:7])
    try:
        return date(year, month, day)
    except ValueError as exc:
        raise ValueError("date") from exc
