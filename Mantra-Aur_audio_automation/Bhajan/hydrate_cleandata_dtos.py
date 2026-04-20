#!/usr/bin/env python3
"""Replace legacy cleanData.json tracks {name, youtubeUrl} with full DTOs (no tags).

Thumbnail text and image come from BhajanAudio.json when the YouTube video id matches.
Otherwise description and Hindi title come from data.tsv; English fields use cleanData name.
streamingOptions[0].contentUrl always uses the exact youtubeUrl from cleanData.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from build_nested_names_youtube import youtube_video_id
from extract_names_youtube_urls import URL_RE, extract_name

HERE = Path(__file__).resolve().parent
DEFAULT_CLEAN = HERE / "cleanData.json"
DEFAULT_AUDIO = HERE / "BhajanAudio.json"
DEFAULT_TSV = HERE / "data.tsv"

_MP3_ONLY = re.compile(r"^[\w\-]+\.mp3$", re.I)


def _is_legacy_track(d: dict) -> bool:
    return isinstance(d.get("youtubeUrl"), str) and "streamingOptions" not in d


def _pick_tsv_description(parts: list[str], url_idx: int) -> str:
    """Prefer cell after URL; else last meaningful text column before URL."""

    def usable(s: str) -> bool:
        s = s.strip()
        if not s:
            return False
        if URL_RE.search(s):
            return False
        if _MP3_ONLY.match(s):
            return False
        return True

    if url_idx + 1 < len(parts):
        after = parts[url_idx + 1].strip()
        if usable(after):
            return after
    for j in range(url_idx - 1, -1, -1):
        c = parts[j].strip()
        if not c or URL_RE.search(c):
            continue
        if re.match(r"^\d+$", c):
            continue
        if c in ("-", "–", "—"):
            continue
        return c
    return ""


def build_tsv_video_id_fallback(path: Path) -> dict[str, tuple[str, str]]:
    """video_id -> (hindi_title, hindi_description). First row per id wins."""
    out: dict[str, tuple[str, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        url_idx = next((i for i, p in enumerate(parts) if URL_RE.search(p)), None)
        if url_idx is None:
            continue
        url = URL_RE.search(parts[url_idx])
        if not url:
            continue
        vid = youtube_video_id(url.group(0))
        if not vid or vid in out:
            continue
        hi_title = extract_name(parts, url_idx).strip()
        hi_desc = _pick_tsv_description(parts, url_idx).strip()
        out[vid] = (hi_title, hi_desc)
    return out


def _copy_thumbnail_from_bhajan(thumb: dict) -> dict:
    title = thumb.get("title") or {}
    desc = thumb.get("description") or {}
    hi_t = title.get("hi")
    en_t = title.get("en")
    hi_d = desc.get("hi") if isinstance(desc, dict) else None
    en_d = desc.get("en") if isinstance(desc, dict) else None
    return {
        "title": {
            "hi": (hi_t if hi_t is not None else "") or "",
            "en": (en_t if en_t is not None else "") or "",
        },
        "imageUrl": thumb.get("imageUrl"),
        "iconUrl": thumb.get("iconUrl"),
        "description": {
            "hi": (hi_d if hi_d is not None else "") or "",
            "en": (en_d if en_d is not None else "") or "",
        },
        "displayOrientation": (thumb.get("displayOrientation") or "SQUARE"),
    }


def _norm_image_url(u: object) -> str | None:
    if u is None:
        return None
    if not isinstance(u, str) or not u.strip():
        return None
    return u.strip()


def build_bhajan_thumbnail_by_vid(path: Path) -> tuple[dict[str, dict], int]:
    """First DTO per video_id -> thumbnail dict. Returns (index, duplicate_skipped_count)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    dups = 0
    for item in data:
        opts = item.get("streamingOptions") or []
        if not opts:
            continue
        url = (opts[0] or {}).get("contentUrl") or ""
        vid = youtube_video_id(str(url))
        if not vid:
            continue
        if vid in out:
            dups += 1
            continue
        out[vid] = _copy_thumbnail_from_bhajan(item.get("thumbnail") or {})
    return out, dups


def _build_dto(
    legacy: dict,
    vid: str | None,
    bhajan_by_vid: dict[str, dict],
    tsv_by_vid: dict[str, tuple[str, str]],
    stats: dict[str, int],
    gaps: list[str],
) -> dict:
    name_en = (legacy.get("name") or "").strip()
    yurl = (legacy.get("youtubeUrl") or "").strip()

    thumb: dict
    if vid and vid in bhajan_by_vid:
        stats["from_bhajan"] += 1
        thumb = json.loads(json.dumps(bhajan_by_vid[vid], ensure_ascii=False))
        thumb["imageUrl"] = _norm_image_url(thumb.get("imageUrl"))
    elif vid and vid in tsv_by_vid:
        stats["from_tsv_only"] += 1
        hi_title, hi_desc = tsv_by_vid[vid]
        if not hi_title:
            hi_title = name_en
        desc_hi = hi_desc or hi_title
        thumb = {
            "title": {"hi": hi_title, "en": name_en},
            "imageUrl": None,
            "iconUrl": None,
            "description": {"hi": desc_hi, "en": name_en},
            "displayOrientation": "SQUARE",
        }
    else:
        stats["no_fallback"] += 1
        gaps.append(f"video_id={vid!r} name={name_en!r} url={yurl[:80]!r}")
        thumb = {
            "title": {"hi": name_en, "en": name_en},
            "imageUrl": None,
            "iconUrl": None,
            "description": {"hi": name_en, "en": name_en},
            "displayOrientation": "SQUARE",
        }

    if thumb.get("iconUrl") is not None and not isinstance(thumb.get("iconUrl"), str):
        thumb["iconUrl"] = None

    return {
        "thumbnail": thumb,
        "streamingOptions": [
            {
                "contentUrl": yurl,
                "streamingQuality": "ADAPTIVE",
                "awsKey": None,
                "sizeInKb": 0,
            }
        ],
        "status": "DRAFT",
        "locked": False,
    }


def walk_hydrate(
    node: dict,
    bhajan_by_vid: dict[str, dict],
    tsv_by_vid: dict[str, tuple[str, str]],
    stats: dict[str, int],
    gaps: list[str],
) -> None:
    for _k, v in node.items():
        if isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict) and _is_legacy_track(item):
                    stats["tracks_total"] += 1
                    yurl = (item.get("youtubeUrl") or "").strip()
                    vid = youtube_video_id(yurl) if yurl else None
                    v[i] = _build_dto(item, vid, bhajan_by_vid, tsv_by_vid, stats, gaps)
        elif isinstance(v, dict):
            walk_hydrate(v, bhajan_by_vid, tsv_by_vid, stats, gaps)


def count_dto_tracks(node: dict) -> int:
    n = 0
    for _k, v in node.items():
        if isinstance(v, list):
            for item in v:
                if isinstance(item, dict) and item.get("streamingOptions"):
                    n += 1
        elif isinstance(v, dict):
            n += count_dto_tracks(v)
    return n


def collect_tags_paths(node: dict, prefix: str = "") -> list[str]:
    bad: list[str] = []
    for k, v in node.items():
        p = f"{prefix}.{k}" if prefix else k
        if k == "tags":
            bad.append(p)
        if isinstance(v, dict):
            bad.extend(collect_tags_paths(v, p))
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    bad.extend(collect_tags_paths(item, f"{p}[{i}]"))
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description="Hydrate cleanData.json with full track DTOs.")
    ap.add_argument("--clean-json", type=Path, default=DEFAULT_CLEAN)
    ap.add_argument("--bhajan-audio", type=Path, default=DEFAULT_AUDIO)
    ap.add_argument("--data-tsv", type=Path, default=DEFAULT_TSV)
    ap.add_argument(
        "--write",
        action="store_true",
        help="Write clean-json; default is dry-run (stats only).",
    )
    ap.add_argument(
        "--no-backup",
        action="store_true",
        help="With --write, skip timestamped .bak copy of the output file.",
    )
    args = ap.parse_args()

    bhajan_by_vid, dup_bhajan = build_bhajan_thumbnail_by_vid(args.bhajan_audio)
    tsv_by_vid = build_tsv_video_id_fallback(args.data_tsv)

    data = json.loads(args.clean_json.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        print("Expected top-level JSON object", file=sys.stderr)
        return 1

    stats: dict[str, int] = {
        "tracks_total": 0,
        "from_bhajan": 0,
        "from_tsv_only": 0,
        "no_fallback": 0,
    }
    gaps: list[str] = []
    walk_hydrate(data, bhajan_by_vid, tsv_by_vid, stats, gaps)

    dto_count = count_dto_tracks(data)
    tag_paths = collect_tags_paths(data)

    print(
        f"tracks_total={stats['tracks_total']}, dto_with_streaming={dto_count}, "
        f"from_bhajan={stats['from_bhajan']}, from_tsv_only={stats['from_tsv_only']}, "
        f"no_bhajan_no_tsv={stats['no_fallback']}, duplicate_bhajan_skipped={dup_bhajan}"
    )
    if gaps:
        print(f"no_bhajan_no_tsv samples (max 20):", file=sys.stderr)
        for g in gaps[:20]:
            print(f"  {g}", file=sys.stderr)
        if len(gaps) > 20:
            print(f"  ... and {len(gaps) - 20} more", file=sys.stderr)
    if tag_paths:
        print(f"ERROR: unexpected tags keys at: {tag_paths[:5]}", file=sys.stderr)
        return 1

    if not args.write:
        print("Dry-run only; pass --write to save.")
        return 0

    out_path = args.clean_json
    if not args.no_backup:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        bak = out_path.with_suffix(out_path.suffix + f".{ts}.bak")
        shutil.copy2(out_path, bak)
        print(f"Backup: {bak}")

    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
