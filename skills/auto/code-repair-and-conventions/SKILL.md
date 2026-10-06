---
name: code-repair-and-conventions
description: Use when fixing code bugs and enforcing exact organizational coding conventions including type hints, regression tests, changelog updates, and CSV quoting.
---
1. Identify all public functions (names not starting with '_') and add type annotations on all parameters and return values.
2. Fix bugs by reading the input and specification, implementing the correct logic, writing outputs, reopening and validating them, and fixing concrete failures.
3. For CSV output functions, ensure proper quoting of fields containing commas or double quotes by wrapping them in double quotes and escaping internal quotes as per CSV standards.
4. For price parsing, handle all documented formats including accounting-style negatives (parentheses) and thousands separators.
5. For rounding monetary values, use half-up rounding as specified.
6. Add a regression test file `tests/test_regressions.py` with one test function per bug fixed; ensure this file passes all tests.
7. Record each fix in `CHANGELOG.md` under the heading '## Unreleased' as a bullet with the format `- fix(<function name>): <short description>`.
8. Do not modify original test files in `tests/`; new test files are allowed.
9. Run the full test suite after changes to verify all tests pass.
10. Stop after all failures are fixed and tests pass.
