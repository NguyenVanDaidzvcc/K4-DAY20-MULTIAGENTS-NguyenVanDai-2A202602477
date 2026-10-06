---
name: tabular-data-and-reporting
description: Use when processing tabular input data with strict schema and metadata conventions, including date parsing, deduplication, filtering, and monetary unit normalization.
---
1. Read the data dictionary before processing to understand all field formats and keys.
2. Parse every documented date format explicitly: use `datetime.strptime` for slash dates (e.g. '%d/%m/%Y'), and `dateutil.parser.isoparse` or `datetime.fromisoformat` for ISO-8601 timestamps.
3. Convert all timezone-aware datetimes to UTC and format as naive UTC datetime strings in ISO 8601 format with 'Z' suffix (YYYY-MM-DDTHH:MM:SSZ).
4. Deduplicate rows by the documented identity key (e.g., order_id), keeping the first occurrence.
5. Count missing values before filtering; exclude rows with missing or invalid amounts (e.g., amount = -999).
6. Normalize region names to canonical spelling exactly: North, South, East, West.
7. Convert all monetary values to integer cents (e.g., 1606.67 USD → 160667) in both JSON aggregates and cleaned CSV cells.
8. Write cleaned CSV output to `workspace/clean.csv` with exact header and column order: `order_id,timestamp_utc,region,amount_cents`.
9. Include one row per distinct record with a known amount.
10. Write metadata JSON to `workspace/answer.json` with keys: `"meta": {"source": <basename of input file>, "rows_in": <count of input rows including duplicates>, "rows_used": <count of distinct records with a known amount>}` plus any required aggregates.
11. Reopen and validate all output files to ensure monetary fields are integers, timestamps are correctly formatted, and row counts match actual processed data.
12. Stop after all outputs are written and validated.
