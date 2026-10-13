"""Command line interface for tool-text-budget."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class InputError(Exception):
    """An input could not be validated against the public contract."""


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise InputError


def _json_load(data: str) -> Any:
    try:
        return json.loads(data, object_pairs_hook=_object_without_duplicates,
                          parse_constant=_reject_constant)
    except (ValueError, TypeError, RecursionError):
        raise InputError from None


def _read_bytes(path: str) -> bytes:
    try:
        return Path(path).read_bytes()
    except (OSError, ValueError):
        raise InputError from None


def _policy(data: bytes) -> tuple[int, int]:
    try:
        decoded = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise InputError from None
    obj = _json_load(decoded)
    if not isinstance(obj, dict) or set(obj) != {"max_record_bytes", "max_total_bytes"}:
        raise InputError
    record = obj["max_record_bytes"]
    total = obj["max_total_bytes"]
    if (type(record) is not int or record < 0 or type(total) is not int or total < 0):
        raise InputError
    return record, total


def _lines(data: bytes) -> list[bytes]:
    """Split only on LF, CRLF, and CR, excluding one final terminator."""
    if not data:
        return []
    result: list[bytes] = []
    start = 0
    i = 0
    while i < len(data):
        if data[i] == 10 or data[i] == 13:
            result.append(data[start:i])
            if data[i] == 13 and i + 1 < len(data) and data[i + 1] == 10:
                i += 1
            start = i + 1
        i += 1
    if start < len(data):
        result.append(data[start:])
    return result


def _utf8_size(text: str) -> int:
    """Encode JSON's valid UTF-16 escape pairs as their Unicode scalar value."""
    normalized: list[str] = []
    i = 0
    while i < len(text):
        code = ord(text[i])
        if 0xD800 <= code <= 0xDBFF:
            if i + 1 >= len(text):
                raise InputError
            low = ord(text[i + 1])
            if not 0xDC00 <= low <= 0xDFFF:
                raise InputError
            normalized.append(chr(0x10000 + ((code - 0xD800) << 10) + (low - 0xDC00)))
            i += 2
            continue
        if 0xDC00 <= code <= 0xDFFF:
            raise InputError
        normalized.append(text[i])
        i += 1
    return len("".join(normalized).encode("utf-8", errors="strict"))


def check(results_data: bytes, policy_data: bytes) -> dict[str, Any]:
    max_record, max_total = _policy(policy_data)
    sizes: list[int] = []
    for raw_line in _lines(results_data):
        if not raw_line:
            raise InputError
        try:
            line = raw_line.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            raise InputError from None
        obj = _json_load(line)
        if not isinstance(obj, dict) or set(obj) != {"text"} or not isinstance(obj["text"], str):
            raise InputError
        size = _utf8_size(obj["text"])
        sizes.append(size)
    total_bytes = sum(sizes)
    oversized = [line for line, size in enumerate(sizes, start=1) if size > max_record]
    total_ok = total_bytes <= max_total
    return {
        "status": "within_budget" if not oversized and total_ok else "over_budget",
        "record_count": len(sizes),
        "total_bytes": total_bytes,
        "total_ok": total_ok,
        "oversized_lines": oversized,
    }


def _parser() -> argparse.ArgumentParser:
    class QuietParser(argparse.ArgumentParser):
        def error(self, message: str) -> None:
            raise InputError from None

    parser = QuietParser(
        prog="tool-text-budget",
        description="Check decoded UTF-8 text bytes in a normalized JSONL fixture.",
    )
    parser.add_argument("results", help="JSONL fixture with one {\"text\": string} object per line")
    parser.add_argument("policy", help="JSON policy with max_record_bytes and max_total_bytes")
    return parser


def main() -> int:
    parser = _parser()
    try:
        args = parser.parse_args()
    except InputError:
        print('{"status":"invalid_input"}')
        return 2
    except SystemExit:
        # argparse uses SystemExit(0) after printing its standard help page.
        return 0
    try:
        result = check(_read_bytes(args.results), _read_bytes(args.policy))
    except InputError:
        print('{"status":"invalid_input"}')
        return 2
    print(json.dumps(result, separators=(",", ":"), ensure_ascii=True))
    return 0 if result["status"] == "within_budget" else 1


if __name__ == "__main__":
    raise SystemExit(main())
