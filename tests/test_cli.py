import json
import os
import subprocess
import sys

import pytest

from tool_text_budget.cli import InputError, check


def policy(record=100, total=100):
    return json.dumps({"max_record_bytes": record, "max_total_bytes": total}).encode()


@pytest.mark.parametrize("text,size", [("", 0), ("abc", 3), ("é", 2), ("😀", 4)])
def test_decoded_utf8_sizes_and_inclusive_bounds(text, size):
    row = json.dumps({"text": text}, ensure_ascii=True).encode()
    result = check(row, policy(size, size))
    assert result == {"status": "within_budget", "record_count": 1,
                      "total_bytes": size, "total_ok": True, "oversized_lines": []}


def test_limits_are_independent_and_plus_one_is_over():
    result = check(b'{"text":"abc"}\n{"text":"four"}', policy(3, 10))
    assert result["status"] == "over_budget"
    assert result["oversized_lines"] == [2]
    assert result["total_ok"] is True
    assert result["total_bytes"] == 7
    total = check(b'{"text":"abc"}', policy(3, 2))
    assert total["status"] == "over_budget" and not total["total_ok"]


@pytest.mark.parametrize("data,count", [
    (b"", 0), (b'{"text":"a"}', 1), (b'{"text":"a"}\n', 1),
    (b'{"text":"a"}\r', 1), (b'{"text":"a"}\r\n', 1),
    (b'{"text":"a"}\r{"text":"b"}\n', 2),
])
def test_supported_endings(data, count):
    assert check(data, policy())["record_count"] == count


def test_json_surrogate_pair_decodes_to_utf8_scalar():
    result = check(b'{"text":"\\ud83d\\ude00"}', policy(4, 4))
    assert result["total_bytes"] == 4


@pytest.mark.parametrize("data", [
    b"\n", b'{"text":"a"}\n\n',
    b'{"text":"a","extra":1}', b'{"other":"a"}', b'[]', b'null',
    b'{"text":1}', b'{"text":"x","text":"y"}', b'{"text":"x"} trailing',
    b'{"text":"\\ud800"}', b'{"text":"x"}\v',
    b'{"text":"x"}\xe2\x80\xa8{"text":"y"}',
    b'{"text":"x"}\xff', b'{"text":"x","n":NaN}',
])
def test_invalid_records(data):
    with pytest.raises(InputError):
        check(data, policy())


@pytest.mark.parametrize("data", [
    b'{"max_record_bytes":true,"max_total_bytes":1}',
    b'{"max_record_bytes":1.0,"max_total_bytes":1}',
    b'{"max_record_bytes":-1,"max_total_bytes":1}',
    b'{"max_record_bytes":1,"max_total_bytes":1,"x":0}',
    b'{"max_record_bytes":1,"max_record_bytes":2,"max_total_bytes":1}',
    b'{"max_record_bytes":1,"max_total_bytes":NaN}', b'\xff', b'[]',
])
def test_invalid_policy(data):
    with pytest.raises(InputError):
        check(b"", data)


def test_cli_no_echo_and_exit_codes(tmp_path):
    results = tmp_path / "secret-results.jsonl"
    policy_file = tmp_path / "secret-policy.json"
    results.write_text('{"text":"PRIVATE_SENTINEL"}', encoding="utf-8")
    policy_file.write_bytes(policy(0, 0))
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [env.get("PYTHONPATH"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))]))
    run = subprocess.run([sys.executable, "-m", "tool_text_budget.cli", str(results), str(policy_file)],
                         capture_output=True, text=True, env=env)
    assert run.returncode == 1 and run.stderr == ""
    assert json.loads(run.stdout) == {"status": "over_budget", "record_count": 1,
        "total_bytes": len("PRIVATE_SENTINEL"), "total_ok": False, "oversized_lines": [1]}
    assert "PRIVATE_SENTINEL" not in run.stdout and str(results) not in run.stdout
    results.write_bytes(b'{"text":"ok"}\n\n')
    run = subprocess.run([sys.executable, "-m", "tool_text_budget.cli", str(results), str(policy_file)],
                         capture_output=True, text=True, env=env)
    assert run.returncode == 2 and run.stdout == '{"status":"invalid_input"}\n' and run.stderr == ""


def test_cli_misuse_is_quiet_and_help_is_supported():
    env = os.environ.copy()
    run = subprocess.run([sys.executable, "-m", "tool_text_budget.cli"], capture_output=True, text=True, env=env)
    assert run.returncode == 2 and run.stdout == '{"status":"invalid_input"}\n' and run.stderr == ""
    run = subprocess.run([sys.executable, "-m", "tool_text_budget.cli", "--help"], capture_output=True, text=True, env=env)
    assert run.returncode == 0 and "usage:" in run.stdout.lower() and run.stderr == ""
