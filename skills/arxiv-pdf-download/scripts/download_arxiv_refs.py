from __future__ import annotations

import argparse
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

HEADER_LINE = "Self-Improving Agents in the Era of Experience: A Survey of Self- to Meta-Evolution"
PAGE_MARKER_RE = re.compile(r"^## 第 \d+ 页$")
ARXIV_ID_RE = re.compile(r"arXiv:(\d{4}\.\d{4,5}(?:v\d+)?)|arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5}(?:v\d+)?)", re.IGNORECASE)
DEFAULT_OUTPUT_DIR = Path("paper/pdf/download")
DEFAULT_LOG_DIR = Path("paper/pdf")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download arXiv PDFs from explicit IDs or a markdown reference section.")
    parser.add_argument("--ids", nargs="*", default=[], help="Explicit arXiv IDs such as 2402.03300 or 2402.03300v2")
    parser.add_argument("--markdown-file", help="Markdown file to scan for arXiv IDs")
    parser.add_argument("--start-marker", help="Start marker inside the markdown file")
    parser.add_argument("--end-marker", help="End marker inside the markdown file; captures through that page/section")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory where PDFs will be saved (default: paper/pdf/download)")
    parser.add_argument("--log", help="Markdown log file to write; defaults under paper/pdf/")
    parser.add_argument("--delay-seconds", type=float, default=0.5, help="Delay between downloads to avoid hammering arXiv")
    args = parser.parse_args()

    if not args.ids and not args.markdown_file:
        parser.error("Provide either --ids or --markdown-file.")
    return args


def normalize_id(value: str) -> str:
    value = value.strip()
    value = value.removeprefix("arXiv:")
    value = value.removesuffix(".pdf")
    if value.startswith("https://") or value.startswith("http://"):
        match = ARXIV_ID_RE.search(value)
        if not match:
            raise ValueError(f"Could not extract an arXiv ID from: {value}")
        return next(group for group in match.groups() if group)
    if not re.fullmatch(r"\d{4}\.\d{4,5}(?:v\d+)?", value, re.IGNORECASE):
        raise ValueError(f"Invalid arXiv ID: {value}")
    return value


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def read_markdown_section(path: Path, start_marker: str | None, end_marker: str | None) -> list[str]:
    lines = path.read_text().splitlines()
    start_index = 0
    if start_marker:
        for index, line in enumerate(lines):
            if line.strip() == start_marker:
                start_index = index
                break
        else:
            raise ValueError(f"Start marker not found: {start_marker}")

    stop_index = len(lines)
    if end_marker:
        end_index = None
        for index in range(start_index, len(lines)):
            if lines[index].strip() == end_marker:
                end_index = index
                break
        if end_index is None:
            raise ValueError(f"End marker not found: {end_marker}")
        for index in range(end_index + 1, len(lines)):
            stripped = lines[index].strip()
            if PAGE_MARKER_RE.fullmatch(stripped) and stripped != end_marker:
                stop_index = index
                break

    return lines[start_index:stop_index]


def extract_ids_from_markdown(path: Path, start_marker: str | None, end_marker: str | None) -> list[str]:
    section_lines = read_markdown_section(path, start_marker, end_marker)
    cleaned: list[str] = []
    for raw in section_lines:
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped == "---":
            continue
        if stripped == "References":
            continue
        if stripped == HEADER_LINE:
            continue
        if PAGE_MARKER_RE.fullmatch(stripped):
            continue
        if re.fullmatch(r"\d+", stripped):
            continue
        cleaned.append(stripped)

    ids: list[str] = []
    for line in cleaned:
        for match in ARXIV_ID_RE.finditer(line):
            ids.append(next(group for group in match.groups() if group))
    return dedupe_preserve_order(ids)


def find_existing_pdf(output_dir: Path, arxiv_id: str) -> Path | None:
    candidates = [output_dir / f"{arxiv_id}.pdf"]
    base_id = re.sub(r"v\d+$", "", arxiv_id)
    if base_id != arxiv_id:
        candidates.append(output_dir / f"{base_id}.pdf")
    else:
        candidates.extend(sorted(output_dir.glob(f"{base_id}v*.pdf")))

    for candidate in candidates:
        if candidate.exists() and candidate.stat().st_size > 0:
            return candidate
    return None


def download_pdf(output_dir: Path, arxiv_id: str, delay_seconds: float) -> tuple[str, str, str]:
    existing = find_existing_pdf(output_dir, arxiv_id)
    if existing is not None:
        return (existing.name, "exists", "Matching PDF already exists")

    target = output_dir / f"{arxiv_id}.pdf"
    request = Request(
        f"https://arxiv.org/pdf/{arxiv_id}.pdf",
        headers={"User-Agent": "Claude Code arXiv PDF downloader"},
    )
    temp_path: Path | None = None
    try:
        with urlopen(request, timeout=180) as response, NamedTemporaryFile(delete=False, dir=output_dir) as temp_file:
            temp_path = Path(temp_file.name)
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                temp_file.write(chunk)
        with temp_path.open("rb") as file_obj:
            if file_obj.read(5) != b"%PDF-":
                temp_path.unlink(missing_ok=True)
                return (target.name, "failed", "Response was not a PDF")
        temp_path.replace(target)
        if delay_seconds > 0:
            time.sleep(delay_seconds)
        return (target.name, "success", "Downloaded PDF successfully")
    except HTTPError as exc:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        return (target.name, "failed", f"HTTP {exc.code}")
    except URLError as exc:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        return (target.name, "failed", f"URL error: {exc.reason}")
    except Exception as exc:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        return (target.name, "failed", str(exc))


def default_log_path(args: argparse.Namespace) -> Path:
    if args.log:
        return Path(args.log)
    if args.markdown_file:
        return DEFAULT_LOG_DIR / f"ref-download-{Path(args.markdown_file).name}"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return DEFAULT_LOG_DIR / f"ref-download-log-{timestamp}.md"


def write_log(log_path: Path, source_label: str, output_dir: Path, ids: list[str], rows: list[dict[str, str]]) -> None:
    counts = {"success": 0, "exists": 0, "failed": 0}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1

    def esc(value: str) -> str:
        return value.replace("|", "\\|").replace("\n", " ")

    lines = [
        "# arXiv PDF download log",
        "",
        f"- Source: `{source_label}`",
        f"- Output directory: `{output_dir}`",
        f"- Generated: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "## Summary",
        "",
        f"- arXiv IDs requested / extracted: {len(ids)}",
        f"- Success: {counts.get('success', 0)}",
        f"- Already existed: {counts.get('exists', 0)}",
        f"- Failed: {counts.get('failed', 0)}",
        "",
        "## Results",
        "",
        "| arXiv ID | Output file | Status | Note |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {esc(row['id'])} | {esc(row['file'])} | {row['status']} | {esc(row['note'])} |")
    log_path.write_text("\n".join(lines) + "\n")


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    log_path = default_log_path(args)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    ids: list[str] = []
    source_label = "explicit ids"

    if args.ids:
        for raw_id in args.ids:
            ids.append(normalize_id(raw_id))

    if args.markdown_file:
        markdown_path = Path(args.markdown_file)
        extracted = extract_ids_from_markdown(markdown_path, args.start_marker, args.end_marker)
        ids.extend(extracted)
        marker_bits = [bit for bit in [args.start_marker, args.end_marker] if bit]
        marker_text = " -> ".join(marker_bits) if marker_bits else "full file"
        source_label = f"{markdown_path} ({marker_text})"

    ids = dedupe_preserve_order(ids)
    rows: list[dict[str, str]] = []

    if not ids:
        write_log(
            log_path,
            source_label,
            output_dir,
            ids,
            [{"id": "—", "file": "—", "status": "failed", "note": "No arXiv IDs found"}],
        )
        print(f"No arXiv IDs found. Log written to {log_path}", file=sys.stderr)
        return 1

    for arxiv_id in ids:
        file_name, status, note = download_pdf(output_dir, arxiv_id, args.delay_seconds)
        rows.append({"id": arxiv_id, "file": file_name, "status": status, "note": note})

    write_log(log_path, source_label, output_dir, ids, rows)
    success = sum(1 for row in rows if row["status"] == "success")
    exists = sum(1 for row in rows if row["status"] == "exists")
    failed = sum(1 for row in rows if row["status"] == "failed")
    print(f"Downloaded: {success}, existed: {exists}, failed: {failed}")
    print(f"Output directory: {output_dir}")
    print(f"Log written to: {log_path}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
