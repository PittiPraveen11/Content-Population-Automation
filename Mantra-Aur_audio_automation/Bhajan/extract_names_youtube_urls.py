#!/usr/bin/env python3
"""Build names-youtube-urls.json from data.tsv (grouped by deity / section headers)."""

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_TSV = HERE / "data.tsv"
OUT_JSON = HERE / "names-youtube-urls.json"

SUBSECTIONS = {
    "MANTRA",
    "STOTRAM",
    "CHALISA",
    "ASHTAKAM",
    "STUTI",
    "AARTI",
    "SHLOKAS",
    "BHAJAN",
    "KATHA",
}
SUBSECTIONS_U = {x.upper() for x in SUBSECTIONS}

URL_RE = re.compile(
    r"https?://(?:www\.)?(?:youtube\.com|youtu\.be)[^\s\t\"'<>]*", re.I
)

EMOJI_SUB_HEADER = re.compile(
    r"^(?:🕉️|📜|🙏|🎶|📖|🔥)\s*(.+)$"
)


def slug_key(s: str) -> str:
    s = s.strip()
    if not s:
        return "misc"
    if re.match(r"^[A-Z][A-Z\s']+JI$", s):
        return re.sub(r"\s+", "", s.lower())
    slug = re.sub(r"[^\w\u0900-\u097F]+", "_", s)
    slug = re.sub(r"_+", "_", slug).strip("_").lower()
    slug = re.sub(r"^[^\w\u0900-\u097F]+", "", slug)
    return slug[:100] if slug else "misc"


def is_sparse_header(parts: list[str]) -> bool:
    if not parts or not parts[0].strip():
        return False
    return all(not p.strip() for p in parts[1:])


def should_skip_sparse_subsection(label: str) -> bool:
    label = label.strip()
    m = EMOJI_SUB_HEADER.match(label)
    if not m:
        return False
    rest = m.group(1).lower()
    return any(
        x in rest
        for x in (
            "mantra",
            "stotram",
            "stuti",
            "bhajan",
            "shlok",
            "katha",
            "chalisa",
            "aarti",
        )
    )


def extract_url(line: str) -> str | None:
    m = URL_RE.search(line)
    return m.group(0) if m else None


def extract_name(parts: list[str], url_idx: int) -> str:
    """First meaningful label column before the URL (title), not necessarily adjacent."""
    for j in range(0, url_idx):
        c = parts[j].strip()
        if not c or URL_RE.search(c):
            continue
        if re.match(r"^\d+$", c):
            continue
        if c in ("-", "–", "—"):
            continue
        return c
    return ""


def main() -> None:
    lines = DATA_TSV.read_text(encoding="utf-8").splitlines()
    current_key = "misc"
    out: dict[str, list[dict[str, str]]] = {}

    for line in lines:
        parts = line.split("\t")
        if is_sparse_header(parts):
            label = parts[0].strip()
            if label.upper() in SUBSECTIONS_U:
                continue
            if should_skip_sparse_subsection(label):
                continue
            if re.match(r"^[A-Z][A-Z\s']+JI$", label):
                current_key = slug_key(label)
            else:
                current_key = slug_key(label)
            continue

        url = extract_url(line)
        if not url:
            continue
        url_idx = next((i for i, p in enumerate(parts) if URL_RE.search(p)), None)
        if url_idx is None:
            continue
        name = extract_name(parts, url_idx) or "(no title)"
        out.setdefault(current_key, []).append({"name": name, "youtubeUrl": url})

    OUT_JSON.write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    total = sum(len(v) for v in out.values())
    print(f"Wrote {OUT_JSON} ({len(out)} groups, {total} entries)")


if __name__ == "__main__":
    main()
