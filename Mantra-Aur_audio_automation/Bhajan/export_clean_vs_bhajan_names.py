#!/usr/bin/env python3
"""
Export one row per track in cleanData.json: name from cleanData vs thumbnail.title.en
from BhajanAudio.json (matched by YouTube video id). Writes CSV + JSON.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_CLEAN = HERE / "cleanData.json"
DEFAULT_AUDIO = HERE / "BhajanAudio.json"
DEFAULT_CSV = HERE / "clean_vs_bhajan_names.csv"
DEFAULT_JSON = HERE / "clean_vs_bhajan_names.json"

from build_nested_names_youtube import youtube_video_id


def build_video_id_to_title_en(path: Path) -> dict[str, str]:
    """First DTO per video_id -> stripped thumbnail.title.en (may be empty string)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for item in data:
        opts = item.get("streamingOptions") or []
        if not opts:
            continue
        url = (opts[0] or {}).get("contentUrl") or ""
        if not url:
            continue
        vid = youtube_video_id(url)
        if not vid or vid in out:
            continue
        thumb = item.get("thumbnail") or {}
        title = thumb.get("title") or {}
        en = title.get("en")
        out[vid] = (en if en is not None else "").strip()
    return out


def iter_clean_tracks(data: dict) -> list[tuple[str, str, str, str]]:
    """Ordered list of (topLevel, genre, name, youtubeUrl)."""
    rows: list[tuple[str, str, str, str]] = []
    for top, genres in data.items():
        if not isinstance(genres, dict):
            continue
        for genre, tracks in genres.items():
            if not isinstance(tracks, list):
                continue
            for item in tracks:
                if not isinstance(item, dict):
                    continue
                name = (item.get("name") or "").strip()
                url = (item.get("youtubeUrl") or "").strip()
                if not url:
                    continue
                rows.append((str(top), str(genre), name, url))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Export cleanData name vs BhajanAudio title.en")
    ap.add_argument("--clean-json", type=Path, default=DEFAULT_CLEAN)
    ap.add_argument("--bhajan-audio", type=Path, default=DEFAULT_AUDIO)
    ap.add_argument("--out-csv", type=Path, default=DEFAULT_CSV)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_JSON)
    args = ap.parse_args()

    title_en_by_vid = build_video_id_to_title_en(args.bhajan_audio)
    data = json.loads(args.clean_json.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        print("Expected object at top of clean JSON", file=sys.stderr)
        return 1

    tracks = iter_clean_tracks(data)
    records: list[dict[str, object]] = []

    for i, (top, genre, name_clean, url) in enumerate(tracks, start=1):
        vid = youtube_video_id(url) or ""
        title_en = title_en_by_vid.get(vid, "") if vid else ""
        names_match = bool(vid) and name_clean == title_en
        records.append(
            {
                "rowIndex": i,
                "topLevel": top,
                "genre": genre,
                "nameCleanData": name_clean,
                "youtubeUrl": url,
                "videoId": vid or None,
                "titleEnBhajanAudio": title_en,
                "namesMatch": names_match,
            }
        )

    args.out_json.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    fieldnames = [
        "rowIndex",
        "topLevel",
        "genre",
        "nameCleanData",
        "titleEnBhajanAudio",
        "namesMatch",
        "videoId",
        "youtubeUrl",
    ]
    with args.out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in records:
            row = {k: r[k] for k in fieldnames}
            if row["videoId"] is None:
                row["videoId"] = ""
            w.writerow(row)

    print(f"Wrote {len(records)} rows -> {args.out_csv}")
    print(f"Wrote {len(records)} rows -> {args.out_json}")
    mismatches = sum(1 for r in records if not r["namesMatch"])
    print(f"namesMatch=true: {len(records) - mismatches}, namesMatch=false: {mismatches}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
