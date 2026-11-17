# IBM i transaction reconciliation

A Python 3.11, standard-library-only prototype that reconciles a ledger CSV with a bank CSV:

```console
python -m recon --ledger L.csv --bank B.csv --out report.json
```

Run it from this project directory. The CSV header must contain `txn_id,amount,date`. Dates use IBM i `CYYMMDD`: `C=0` maps to 1900–1999, `C=1` maps to 2000–2099, and `0000000` is a valid absent date.

## Rules

- Keys are trimmed and uppercased. An empty normalized key is invalid.
- Amounts are parsed as finite `Decimal` values and quantized to two fractional digits using `ROUND_HALF_EVEN`. Negative amounts are valid.
- A date must be exactly seven ASCII digits and a real calendar date, except `0000000`, which means no date. A malformed date invalidates the record even when its amount is valid.
- Validation reports only the first problem in this order: key, amount, date. Data row numbering starts at 1 after the CSV header.
- In each file, repeated keys whose rounded amounts are all equal form a duplicate group; the first row is used. A key repeated with differing rounded amounts is a conflict for that file. A conflicted key is excluded from matching and missing-record lists.
- Valid, non-conflicted keys in both files are matched when their rounded amounts agree. Otherwise they are amount mismatches; `delta` is bank amount minus ledger amount. Keys found on only one side are listed as missing on the other side.

## Report format

The JSON report contains `matched`, `missing_in_bank`, `missing_in_ledger`, `amount_mismatches`, `duplicates`, `conflicts`, and `invalid_records`. Monetary values are two-decimal strings. Dates are ISO `YYYY-MM-DD` strings or `null`. Lists are deterministically ordered by key then row where row numbers apply. JSON uses sorted object keys, two-space indentation, and a trailing newline.

Invalid records have `file` (`ledger` or `bank`), one-based data `row`, `reason` (`key`, `amount`, or `date`), and normalized `key` (empty when the key itself is invalid). Duplicate records contain the file, key, rounded amount, and every row in the duplicate group. Conflict records contain the file, key, and each conflicting row with its rounded amount.

## Examples

Sample inputs are in `examples/ledger.csv` and `examples/bank.csv`. To write an example report:

```console
python -m recon --ledger examples/ledger.csv --bank examples/bank.csv --out report.json
```

## Tests

Run the standard-library test suite from this directory:

```console
python -m unittest discover -s tests -v
```

## License

MIT; see [LICENSE](LICENSE).
