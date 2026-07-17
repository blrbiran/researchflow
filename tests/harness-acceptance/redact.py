#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Optional, Pattern, Sequence, Tuple

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
_PRIVATE_SENTINELS: Tuple[str, ...] = (
    "Global Claude Code Configuration",
    "Absolutely Forbidden Operations",
    "Before Any Destructive Operation",
    "Wait for explicit YES",
)
_PRIVATE_PATTERNS: Tuple[Tuple[str, Pattern[str]], ...] = tuple(
    ("private_instruction_fragment", re.compile(rf"(?P<match>{re.escape(sentinel)})"))
    for sentinel in _PRIVATE_SENTINELS
)
_ABSOLUTE_PATH_RE = re.compile(r"(?P<match>(?<![A-Za-z0-9:/])/[^\s\"'<>),;]+)")
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


def _compile_allowed_absolute_patterns(patterns: Optional[Sequence[str]]) -> list[Pattern[str]]:
    compiled: list[Pattern[str]] = []
    for pattern in patterns or ():
        compiled.append(re.compile(pattern))
    return compiled


def _normalize_committed_roots(committed_roots: Optional[Sequence[Path]]) -> list[Path]:
    normalized: list[Path] = []
    for root in committed_roots or ():
        path = Path(root)
        if not path.is_absolute():
            raise ValueError("committed roots must be absolute paths")
        normalized.append(path.resolve(strict=False))
    return normalized


def _path_is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _scan_absolute_paths(
    text: str,
    forbidden_home: Optional[str],
    committed_roots: Sequence[Path],
    allowed_absolute_patterns: Sequence[Pattern[str]],
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for matched in _ABSOLUTE_PATH_RE.finditer(text):
        candidate = matched.group("match")
        if candidate.startswith(("/Users/", "/home/")):
            continue
        if forbidden_home and candidate.startswith(forbidden_home):
            continue
        if any(pattern.fullmatch(candidate) for pattern in allowed_absolute_patterns):
            continue
        rule = "absolute_path"
        resolved_candidate = Path(candidate).resolve(strict=False)
        if any(_path_is_relative_to(resolved_candidate, root) for root in committed_roots):
            rule = "repo_absolute_path"
        hits.append(_make_hit(rule, text, matched))
    return hits


def scan_text(
    text: str,
    forbidden_home: Optional[str],
    committed_roots: Optional[Sequence[Path]] = None,
    allowed_absolute_patterns: Optional[Sequence[str]] = None,
) -> list[dict[str, Any]]:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    compiled_allowed_patterns = _compile_allowed_absolute_patterns(allowed_absolute_patterns)
    normalized_roots = _normalize_committed_roots(committed_roots)
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
    hits.extend(_scan_patterns(text, _PRIVATE_PATTERNS))
    hits.extend(_scan_absolute_paths(text, forbidden_home, normalized_roots, compiled_allowed_patterns))
    hits.sort(key=lambda item: (item["line"], item["column"], item["rule"], item["match"]))
    return hits


def scan_tree(
    tree: Path,
    forbidden_home: Optional[str] = None,
    committed_roots: Optional[Sequence[Path]] = None,
    allowed_absolute_patterns: Optional[Sequence[str]] = None,
) -> list[dict[str, Any]]:
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
        for hit in scan_text(
            text,
            forbidden_home,
            committed_roots=committed_roots,
            allowed_absolute_patterns=allowed_absolute_patterns,
        ):
            file_hit = dict(hit)
            file_hit["path"] = str(path.relative_to(tree))
            hits.append(file_hit)
    return hits


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tree", required=True)
    parser.add_argument("--forbidden-home")
    parser.add_argument("--committed-root", action="append", default=[])
    parser.add_argument("--allow-absolute-pattern", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    tree = Path(args.tree)
    committed_roots = [Path(item) for item in args.committed_root]
    hits = scan_tree(
        tree,
        args.forbidden_home,
        committed_roots=committed_roots,
        allowed_absolute_patterns=args.allow_absolute_pattern,
    )
    if hits:
        json.dump(hits, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
