# Independent release review: issue #3 / PR #2

**Decision: PASS for the frozen contract at `118cb325bba535af1a1923228d145376b2325947`.** This is a review result only; it does not publish a release.

## Target and scope

- Repository: `Hardik-S/tool-text-budget`
- Issue: [#3](https://github.com/Hardik-S/tool-text-budget/issues/3)
- PR: [#2](https://github.com/Hardik-S/tool-text-budget/pull/2), `feature/issue-1-text-budget` into `main`
- Reviewed commit SHA: `118cb325bba535af1a1923228d145376b2325947`
- Contract: `CONTRACT.md` at that commit
- Review scope: runtime behavior, installed quickstart, examples, docs, tests, CI status. No implementation files changed.

## Evidence

1. **Clean isolated install and full suite.** Copied the target commit's package, tests, examples, README, launch note, license, and `pyproject.toml` to a fresh temporary checkout, created a fresh Python 3.13.1 venv, and ran the documented install:
   - `python -m pip install -e ".[test]"` — succeeded (`tool-text-budget==0.1.0`, `pytest==9.1.1`).
   - `python -m pytest -q -ra` — `36 passed in 1.09s`; no skips.
   - Temporary checkout: `C:\Users\hshre\AppData\Local\Temp\tool-text-budget-review-a9b7ac2aa68c4decbaf59ff12cb48049`.
2. **Installed public examples** (`.venv\Scripts\tool-text-budget.exe`):
   - within pair: exit `0`, `within_budget`, 2 records / 18 bytes / `total_ok=true` / no oversized lines.
   - over pair: exit `1`, `over_budget`, 2 records / 52 bytes / `total_ok=false` / oversized line `[2]`.
   - malformed JSONL and boolean-policy examples: each exit `2`, stdout `{"status":"invalid_input"}`, stderr empty.
3. **Installed adversarial CLI probes — PASS.** The script drove the installed entry point and asserted status, exit code, parsed summary, and empty stderr. Covered empty file and empty text at a zero-byte limit; exact and plus-one record and aggregate bounds; literal UTF-8 and JSON-escaped Unicode (including a surrogate pair); LF, CR, and CRLF; blank records; duplicate keys; lone high/low surrogates; Unicode line separator; malformed UTF-8; malformed JSON suffix; no-argument misuse; and `--help`. Invalid-input output remained the fixed JSON object without leaking probe data.
4. **Remote CI on PR #2:** `gh pr checks 2 --repo Hardik-S/tool-text-budget` showed GitGuardian Security Checks passing and both reported CI runs passing their Ubuntu/Windows × Python 3.10/3.13 matrix jobs (8 matrix job entries total, no failures or pending checks).
5. **Docs/example consistency:** README and `LAUNCH.md` describe the observed exit codes and invalid-input output; `within` and `over` fixtures agree with their configured byte limits; the invalid fixtures exercise malformed JSONL and a boolean policy value. Scope and memory caveats match the contract.

## Contract coverage notes

- Byte counts are based on decoded text only. Exact bounds are inclusive; one-byte-over record and total cases are reported independently.
- Empty input, empty text, all three supported line terminators, Unicode scalar encoding, and valid escaped surrogate pairs behave as specified.
- Wrong shapes/types, booleans as policy integers, duplicate keys, non-finite constants, malformed UTF-8/JSON, blank records, unsupported Unicode separators, and unpaired surrogates are rejected before a budget result.
- Normal and invalid summaries do not include text, paths, policy values, hashes, or exception details. The standard help page is available; CLI misuse is quiet and exits `2`.

## Limits and gaps

- Local installed verification was on Windows / Python 3.13.1. Python 3.10 and Ubuntu behavior is supported by the passing PR CI matrix, not a local run in this review.
- Resource-exhaustion behavior for arbitrarily large files was not stress-tested; the contract explicitly notes input-sized memory use.
- This review did not publish/tag a release or alter source/docs. PR #2 was open when reviewed; check status is a point-in-time observation.

## Reproduction commands

From a clean copy of the reviewed commit:

```powershell
python -m venv .venv
# Activate the environment
python -m pip install -e ".[test]"
python -m pytest -q -ra
tool-text-budget examples/within.jsonl examples/within-policy.json
# Expected exit code: 0
tool-text-budget examples/over.jsonl examples/over-policy.json
# Expected exit code: 1
tool-text-budget examples/invalid.jsonl examples/within-policy.json
# Expected exit code: 2; stdout is only {"status":"invalid_input"}, stderr is empty
tool-text-budget examples/within.jsonl examples/invalid-policy.json
# Expected exit code: 2; stdout is only {"status":"invalid_input"}, stderr is empty
gh pr checks 2 --repo Hardik-S/tool-text-budget
```

The adversarial probes described above were an additional inline Python harness against the installed `tool-text-budget.exe`; their assertions all passed.
