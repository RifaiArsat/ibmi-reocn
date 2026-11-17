"""Command-line entry point."""

import argparse
from dataclasses import asdict
from pathlib import Path

from .loader import load_csv
from .matcher import reconcile
from .report import render_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reconcile an IBM i ledger CSV against a bank CSV.")
    parser.add_argument("--ledger", required=True, help="ledger CSV path")
    parser.add_argument("--bank", required=True, help="bank CSV path")
    parser.add_argument("--out", required=True, help="output JSON report path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        ledger, ledger_invalid = load_csv(args.ledger, "ledger")
        bank, bank_invalid = load_csv(args.bank, "bank")
        report = reconcile(ledger, bank)
        invalid = [asdict(item) for item in ledger_invalid + bank_invalid]
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_report(report, invalid), encoding="utf-8", newline="")
    except (OSError, ValueError) as exc:
        build_parser().error(str(exc))
    return 0
