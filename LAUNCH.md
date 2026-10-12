# Launch notes

1. Create a Python 3.10 or newer environment and install the package with `python -m pip install -e ".[test]"`.
2. Run `python -m pytest` and confirm there are no skipped tests.
3. Check the three examples: `tool-text-budget examples/within.jsonl examples/within-policy.json` exits 0; the `over` pair exits 1; the `invalid` pair exits 2 and emits only the fixed invalid-input JSON line.
4. Use `tool-text-budget RESULTS.jsonl POLICY.json` on locally prepared, normalized fixtures. Review the numeric summary without placing sensitive text in logs.

CI covers Ubuntu and Windows on Python 3.10 and 3.13. Package version `0.1.0` is the initial launch version.
