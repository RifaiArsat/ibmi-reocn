import csv
import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from recon.loader import load_csv
from recon.matcher import reconcile
from recon.normalize import normalize_key, parse_amount, parse_ibmi_date


ROOT = Path(__file__).resolve().parents[1]


class NormalizeTests(unittest.TestCase):
    def test_key_trims_and_uppercases(self):
        self.assertEqual(normalize_key("  aBc  "), "ABC")

    def test_ibmi_dates_and_zero_date(self):
        self.assertEqual(parse_ibmi_date("1261117").isoformat(), "2026-11-17")
        self.assertEqual(parse_ibmi_date("0990102").isoformat(), "1999-01-02")
        self.assertIsNone(parse_ibmi_date("0000000"))

    def test_impossible_date_rejected(self):
        with self.assertRaises(ValueError):
            parse_ibmi_date("1260231")


class LoaderTests(unittest.TestCase):
    def write_csv(self, path, rows):
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["txn_id", "amount", "date"])
            writer.writerows(rows)

    def test_invalid_reason_precedence_and_row_numbers(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "in.csv"
            self.write_csv(path, [
                [" ", "bad", "bad"],
                ["X", "bad", "bad"],
                ["Y", "1.00", "1260231"],
                ["Z", "-1.005", "0000000"],
            ])
            records, invalid = load_csv(path, "ledger")
        self.assertEqual([(x.row, x.reason) for x in invalid], [(1, "key"), (2, "amount"), (3, "date")])
        self.assertEqual(records[0].amount, Decimal("-1.00"))
        self.assertIsNone(records[0].date)

class MatchingTests(unittest.TestCase):
    def record(self, key, amount, row, date=None):
        from recon.loader import Transaction
        return Transaction(key, Decimal(amount), date, row)

    def test_matching_mismatch_missing_and_duplicates(self):
        ledger = [self.record("A", "10.00", 1), self.record("A", "10.00", 2), self.record("B", "5.00", 3), self.record("C", "1.00", 4)]
        bank = [self.record("A", "10.00", 1), self.record("B", "7.00", 2), self.record("D", "2.00", 3)]
        report = reconcile(ledger, bank)
        self.assertEqual([x["key"] for x in report["matched"]], ["A"])
        self.assertEqual(report["amount_mismatches"][0]["delta"], "2.00")
        self.assertEqual(report["missing_in_bank"][0]["key"], "C")
        self.assertEqual(report["missing_in_ledger"][0]["key"], "D")
        self.assertEqual(report["duplicates"][0]["rows"], [1, 2])

class CliTests(unittest.TestCase):
    def test_cli_writes_sorted_json_with_newline(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            ledger, bank, out = folder / "ledger.csv", folder / "bank.csv", folder / "out" / "report.json"
            ledger.write_text("txn_id,amount,date\nA,1.00,1260101\n,2.00,1260101\n", encoding="utf-8")
            bank.write_text("txn_id,amount,date\nA,1.01,1260102\n", encoding="utf-8")
            result = subprocess.run([sys.executable, "-m", "recon", "--ledger", str(ledger), "--bank", str(bank), "--out", str(out)], cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            raw = out.read_text(encoding="utf-8")
            self.assertTrue(raw.endswith("\n"))
            report = json.loads(raw)
            self.assertEqual(report["amount_mismatches"][0]["delta"], "0.01")
            self.assertEqual(report["invalid_records"], [{"file": "ledger", "key": "", "reason": "key", "row": 2}])


if __name__ == "__main__":
    unittest.main()
