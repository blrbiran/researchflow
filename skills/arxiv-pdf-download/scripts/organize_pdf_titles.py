from __future__ import annotations

import argparse
import hashlib
import os
import re
import time
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    import fitz  # type: ignore
except Exception:
    fitz = None

ARXIV_NAME_RE = re.compile(r"^(\d{4}\.\d{4,5}(?:v\d+)?)\.pdf$", re.IGNORECASE)
DEFAULT_STAGING_DIR = Path("paper/pdf/download")
DEFAULT_CANONICAL_DIR = Path("paper/pdf")
DEFAULT_ARXIV_DIR = Path("paper/pdf/arxiv")
TITLE_CHAR_REPLACEMENTS = {
    " ": " ",
    "/": " ",
    "\\": " ",
    ":": " ",
    "*": " ",
    "?": " ",
    '"': "",
    "<": "",
    ">": "",
    "|": " ",
    "：": " ",
    "／": " ",
    "＼": " ",
    "？": " ",
    "＊": " ",
    "｜": " ",
    "“": "",
    "”": "",
    "‘": "",
    "’": "",
}


@dataclass
class PlannedAction:
    source_name: str
    status: str
    canonical_name: str | None
    note: str
    create_symlink: bool = False
    symlink_name: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rename staged PDFs by title and create arXiv filename symlinks.")
    parser.add_argument("--staging-dir", default=str(DEFAULT_STAGING_DIR), help="Directory containing raw PDFs (default: paper/pdf/download)")
    parser.add_argument("--canonical-dir", default=str(DEFAULT_CANONICAL_DIR), help="Directory for title-based PDFs (default: paper/pdf)")
    parser.add_argument("--arxiv-dir", default=str(DEFAULT_ARXIV_DIR), help="Directory for arXiv filename symlinks (default: paper/pdf/arxiv)")
    parser.add_argument("--apply", action="store_true", help="Apply file moves and symlink creation; omit for preview only")
    return parser.parse_args()


def sanitize_title(title: str) -> str:
    title = unicodedata.normalize("NFKC", title)
    for old, new in TITLE_CHAR_REPLACEMENTS.items():
        title = title.replace(old, new)
    title = "".join(ch for ch in title if unicodedata.category(ch)[0] != "C")
    title = re.sub(r"\s+", " ", title).strip().rstrip(".")
    while title and len(title.encode("utf-8")) > 220:
        title = title[:-1].rstrip()
    return title


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_arxiv_titles(ids: list[str]) -> dict[str, str]:
    if not ids:
        return {}
    ns = {"a": "http://www.w3.org/2005/Atom"}
    titles: dict[str, str] = {}
    batch_size = 40
    for index in range(0, len(ids), batch_size):
        batch = ids[index:index + batch_size]
        query = urlencode({"id_list": ",".join(batch)})
        request = Request(
            f"https://export.arxiv.org/api/query?{query}",
            headers={"User-Agent": "Claude Code PDF organizer"},
        )
        with urlopen(request, timeout=60) as response:
            root = ET.fromstring(response.read())
        for entry in root.findall("a:entry", ns):
            id_text = entry.findtext("a:id", default="", namespaces=ns)
            title = entry.findtext("a:title", default="", namespaces=ns)
            if not id_text or not title:
                continue
            paper_id = id_text.rsplit("/abs/", 1)[-1].strip()
            title = " ".join(title.split())
            titles[paper_id] = title
            titles[re.sub(r"v\d+$", "", paper_id)] = title
        if index + batch_size < len(ids):
            time.sleep(3)
    return titles


def valid_meta_title(title: str, stem: str) -> bool:
    title = " ".join(title.split()).strip()
    if not title:
        return False
    low = title.lower()
    if low in {"untitled", "unknown", stem.lower()}:
        return False
    if low.startswith("microsoft word") or low.startswith("acrobat distiller"):
        return False
    return sum(ch.isalpha() for ch in title) >= 8


def heuristic_pdf_title(path: Path) -> str | None:
    if fitz is None:
        return None
    doc = fitz.open(path)
    try:
        meta_title = ((doc.metadata or {}).get("title") or "").strip()
        if valid_meta_title(meta_title, path.stem):
            return " ".join(meta_title.split())

        page = doc[0]
        data = page.get_text("dict")
        lines: list[dict[str, float | str]] = []
        abstract_y = None
        for block in data.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                text = "".join(span.get("text", "") for span in spans)
                text = " ".join(text.split())
                if not text:
                    continue
                y = min(span.get("bbox", [0, 0, 0, 0])[1] for span in spans)
                size = max(span.get("size", 0) for span in spans)
                if text.lower() == "abstract" and abstract_y is None:
                    abstract_y = y
                lines.append({"text": text, "y": y, "size": size})

        if not lines:
            return None

        cutoff_y = abstract_y if abstract_y is not None else 260
        candidates = []
        for item in lines:
            text = str(item["text"])
            low = text.lower()
            if float(item["y"]) > cutoff_y + 5:
                continue
            if "arxiv:" in low or "http" in low or "@" in text:
                continue
            if low in {"abstract", "introduction", "contents"}:
                continue
            if re.fullmatch(r"[0-9 .\-:;,/]+", text):
                continue
            if sum(ch.isalpha() for ch in text) < 6:
                continue
            if any(word in low for word in ["university", "institute", "department", "school of"]):
                continue
            candidates.append(item)

        if not candidates:
            return None

        max_size = max(float(item["size"]) for item in candidates)
        strong = [item for item in candidates if float(item["size"]) >= max_size - 0.8]
        strong.sort(key=lambda item: float(item["y"]))
        if not strong:
            return None

        title_lines = [str(strong[0]["text"])]
        previous_y = float(strong[0]["y"])
        for item in strong[1:]:
            y = float(item["y"])
            if y - previous_y > 35:
                break
            title_lines.append(str(item["text"]))
            previous_y = y
        return " ".join(" ".join(title_lines).split())
    finally:
        doc.close()


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def build_plan(staging_dir: Path, canonical_dir: Path, arxiv_dir: Path) -> list[tuple[Path, PlannedAction]]:
    files = sorted(staging_dir.glob("*.pdf"))
    arxiv_ids = []
    for path in files:
        match = ARXIV_NAME_RE.match(path.name)
        if match:
            arxiv_ids.append(match.group(1))
    arxiv_titles = fetch_arxiv_titles(arxiv_ids)

    plan: list[tuple[Path, PlannedAction]] = []
    hash_cache: dict[Path, str] = {}

    def digest(path: Path) -> str:
        if path not in hash_cache:
            hash_cache[path] = sha256(path)
        return hash_cache[path]

    for path in files:
        arxiv_match = ARXIV_NAME_RE.match(path.name)
        arxiv_id = arxiv_match.group(1) if arxiv_match else None
        title = arxiv_titles.get(arxiv_id or "", "") if arxiv_id else ""
        if not title:
            title = heuristic_pdf_title(path) or ""
        if not title:
            plan.append((path, PlannedAction(path.name, "unresolved-title", None, "Could not determine title")))
            continue

        safe_title = sanitize_title(title)
        if not safe_title:
            plan.append((path, PlannedAction(path.name, "unresolved-title", None, "Title became empty after sanitization")))
            continue

        canonical_name = f"{safe_title}.pdf"
        target = canonical_dir / canonical_name
        symlink_name = path.name if arxiv_id else None
        symlink_path = arxiv_dir / symlink_name if symlink_name else None

        if target.exists():
            same_content = digest(path) == digest(target)
            if same_content:
                create_symlink = bool(symlink_path and not symlink_path.exists())
                note = "Same-content duplicate of existing canonical file"
                plan.append((path, PlannedAction(path.name, "duplicate-same-content", canonical_name, note, create_symlink, symlink_name)))
            else:
                note = "Different-content title collision with existing canonical file"
                plan.append((path, PlannedAction(path.name, "title-collision", canonical_name, note)))
            continue

        plan.append((path, PlannedAction(path.name, "move", canonical_name, "Move to canonical title filename", bool(arxiv_id), symlink_name)))

    return plan


def apply_plan(plan: list[tuple[Path, PlannedAction]], canonical_dir: Path, arxiv_dir: Path) -> None:
    for source_path, action in plan:
        if action.status == "move":
            target = canonical_dir / action.canonical_name
            source_path.rename(target)
            if action.create_symlink and action.symlink_name:
                symlink_path = arxiv_dir / action.symlink_name
                if not symlink_path.exists():
                    rel_target = os.path.relpath(target, arxiv_dir)
                    symlink_path.symlink_to(rel_target)
        elif action.status == "duplicate-same-content" and action.create_symlink and action.symlink_name and action.canonical_name:
            target = canonical_dir / action.canonical_name
            symlink_path = arxiv_dir / action.symlink_name
            if not symlink_path.exists():
                rel_target = os.path.relpath(target, arxiv_dir)
                symlink_path.symlink_to(rel_target)


def main() -> int:
    args = parse_args()
    staging_dir = Path(args.staging_dir)
    canonical_dir = Path(args.canonical_dir)
    arxiv_dir = Path(args.arxiv_dir)

    ensure_directory(staging_dir)
    ensure_directory(canonical_dir)
    ensure_directory(arxiv_dir)

    plan = build_plan(staging_dir, canonical_dir, arxiv_dir)

    summary = {
        "move": 0,
        "duplicate-same-content": 0,
        "title-collision": 0,
        "unresolved-title": 0,
        "symlink-create": 0,
    }
    for _, action in plan:
        summary[action.status] = summary.get(action.status, 0) + 1
        if action.create_symlink:
            summary["symlink-create"] += 1

    mode = "APPLY" if args.apply else "PREVIEW"
    print(f"Mode: {mode}")
    print(f"Staging directory: {staging_dir}")
    print(f"Canonical directory: {canonical_dir}")
    print(f"arXiv symlink directory: {arxiv_dir}")
    print()
    print("Summary:")
    for key in ["move", "duplicate-same-content", "title-collision", "unresolved-title", "symlink-create"]:
        print(f"- {key}: {summary.get(key, 0)}")
    print()
    print("Planned actions:")
    for _, action in plan:
        canonical = action.canonical_name or "—"
        symlink = action.symlink_name or "—"
        extra = f" | symlink {symlink}" if action.create_symlink and action.symlink_name else ""
        print(f"- {action.source_name} -> [{action.status}] {canonical} | {action.note}{extra}")

    if args.apply:
        apply_plan(plan, canonical_dir, arxiv_dir)
        print()
        print("Applied rename / move / symlink operations.")
    else:
        print()
        print("Preview only. Re-run with --apply after user confirmation.")

    if summary.get("title-collision", 0) or summary.get("unresolved-title", 0):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
