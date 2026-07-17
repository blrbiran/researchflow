#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Optional, Pattern, Tuple

_HASH_HEX_RE = re.compile(r"\b[0-9a-f]{64}\b")
_HOME_PATTERNS: Tuple[Tuple[str, Pattern[str]], ...] = (
    ("home_path", re.compile(r"(?P<match>/Users/[^\s\"'<>]+)")),
    ("home_path", re.compile(r"(?P<match>/home/[^\s\"'<>]+)")),
    ("home_path", re.compile(r"(?P<match>~/(?:[^\s\"'<>]+)?)")),
)
_FIELD_PATTERNS: Tuple[Tuple[str, Pattern[str]], ...] = (
    (
        "base_url",
        re.compile(
            r"(?P<match>(?i:[\"']?(?:base_url|baseurl|api_base|api_url|endpoint_url)[\"']?\s*[:=]\s*[\"']?https?://[^\s\"'}]+))"
        ),
    ),
    (
        "authorization_header",
        re.compile(
            r"(?P<match>(?i:\bAuthorization\b\s*[:=]\s*[\"']?Bearer\s+[^\s\"'}]+))"
        ),
    ),
    (
        "bearer_token",
        re.compile(r"(?P<match>(?i:\bBearer\s+[A-Za-z0-9._~-]{12,}))"),
    ),
    (
        "api_key_field",
        re.compile(
            r"(?P<match>(?i:\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|credential|credentials|password|secret)\b\s*[:=]\s*[\"']?[^\s\"',}]+))"
        ),
    ),
    ("token_literal", re.compile(r"(?P<match>\b(?:sk|rk)-[A-Za-z0-9]{12,}\b)")),
)
_SKIP_DIRS = {"__pycache__"}
_SKIP_SUFFIXES = {".pyc"}


def _line_col(text: str, index: int) -> tuple[int, int]:
    line = text.count("\n", 0, index) + 1
    line_start = text.rfind("\n", 0, index)
    if line_start == -1:
        column = index + 1
    else:
        column = index - line_start
    return line, column


def _make_hit(rule: str, text: str, matched: re.Match[str]) -> dict[str, Any]:
    line, column = _line_col(text, matched.start())
    return {
        "rule": rule,
        "line": line,
        "column": column,
        "match": matched.group("match"),
    }


def _scan_patterns(text: str, patterns: Iterable[Tuple[str, Pattern[str]]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for rule, pattern in patterns:
        for matched in pattern.finditer(text):
            hit = _make_hit(rule, text, matched)
            if rule == "home_path" and _HASH_HEX_RE.fullmatch(hit["match"]):
                continue
            hits.append(hit)
    return hits


def scan_text(text: str, forbidden_home: Optional[str]) -> list[dict[str, Any]]:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    hits: list[dict[str, Any]] = []
    if forbidden_home:
        start = 0
        while True:
            index = text.find(forbidden_home, start)
            if index == -1:
                break
            line, column = _line_col(text, index)
            hits.append(
                {
                    "rule": "forbidden_home",
                    "line": line,
                    "column": column,
                    "match": forbidden_home,
                }
            )
            start = index + len(forbidden_home)
    hits.extend(_scan_patterns(text, _HOME_PATTERNS))
    hits.extend(_scan_patterns(text, _FIELD_PATTERNS))
    hits.sort(key=lambda item: (item["line"], item["column"], item["rule"], item["match"]))
    return hits


def scan_tree(tree: Path, forbidden_home: Optional[str] = None) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for path in sorted(tree.rglob("*")):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.is_dir() or path.suffix in _SKIP_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            hits.append(
                {
                    "path": str(path.relative_to(tree)),
                    "rule": "non_utf8",
                    "line": 1,
                    "column": 1,
                    "match": "<binary>",
                }
            )
            continue
        for hit in scan_text(text, forbidden_home):
            file_hit = dict(hit)
            file_hit["path"] = str(path.relative_to(tree))
            hits.append(file_hit)
    return hits


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tree", required=True)
    parser.add_argument("--forbidden-home")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    tree = Path(args.tree)
    hits = scan_tree(tree, args.forbidden_home)
    if hits:
        json.dump(hits, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
