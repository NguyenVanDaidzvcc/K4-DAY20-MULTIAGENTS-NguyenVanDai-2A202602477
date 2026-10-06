---
name: log-triage-and-reporting
description: Use when parsing log files to extract error entries, normalize service names, timestamps, and produce sorted error reports with repeat counts.
---
1. Read the entire log file and parse each entry line by line.
2. Normalize service names to lower-case with hyphens replaced by underscores (e.g., payment-service → payment_service).
3. Filter entries to include only those with level ERROR or CRITICAL (case-insensitive).
4. Parse timestamps with timezone awareness, convert all to UTC naive datetime, and format as ISO 8601 strings with 'Z' suffix (YYYY-MM-DDTHH:MM:SSZ).
5. Extract the message text following the service name and level.
6. For entries with tracebacks, capture the last line of the traceback as the `exception` field; if no traceback, set `exception` to null.
7. Detect and sum repeated messages indicated by lines like `-- last message repeated N times --` immediately following an entry; set `repeat_count` to 1 plus repeats.
8. Aggregate counts of errors by normalized service name.
9. Sort the final errors list by service name ascending, then by timestamp_utc ascending.
10. Write output JSON to `workspace/errors.json` with top-level keys: `"schema_version": 2`, `"generated_by": "log-triage"`, `"errors": [...]`, and `"counts_by_service": {...}`.
11. Verify the output file exists and matches all schema and sorting requirements.
12. Stop after writing and validating the output.
