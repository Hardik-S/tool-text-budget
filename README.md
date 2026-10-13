# tool-text-budget

`tool-text-budget` is an offline Python CLI that checks the UTF-8 byte size of decoded text values in normalized JSONL fixtures. It does not inspect JSON syntax size, normalize text, or contact a network service.

## Install and run

```console
python -m venv .venv
# Activate the environment, then:
python -m pip install -e ".[test]"
tool-text-budget examples/within.jsonl examples/within-policy.json
```

The command prints one JSON summary. Exit code `0` means every record and the aggregate fit the inclusive limits; `1` means at least one limit was exceeded; `2` means the invocation or an input was invalid. Invalid input prints only `{"status":"invalid_input"}` to stdout and nothing to stderr. `tool-text-budget --help` describes the arguments.

## Input format

The policy is a UTF-8 JSON object containing exactly two nonnegative integer fields: `max_record_bytes` and `max_total_bytes`. Booleans are not integers for this policy. The results file is UTF-8 JSONL; every record must be an object containing exactly one string field named `text`. Empty files and empty strings are valid. Blank lines, duplicate keys, non-finite JSON constants, malformed UTF-8/JSON, unpaired surrogate values, and wrong fields or types are rejected.

Byte counts are computed after JSON decoding by strictly encoding each `text` value as UTF-8. JSON escaping, record terminators, and other syntax do not count. LF, CRLF, and CR delimit records; Unicode line separators do not. The program validates every input before producing a budget result. It intentionally reports record counts and byte lengths, but never echoes text, policy values, paths, hashes, or exception details.

The examples directory contains within-budget, over-budget, and invalid-input fixtures. The invalid pair includes both malformed JSONL and a boolean policy limit; each is rejected by validation.

## Scope

This utility checks normalized text fixture byte budgets. It is not an MCP protocol validator, tokenizer, context-window predictor, cost calculator, truncator, or secret scanner. Callers are responsible for preparing normalized fixtures. Processing keeps the decoded input in memory.

Run tests with `python -m pytest` after installing the `test` extra.
