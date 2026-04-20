#!/usr/bin/env python3
"""
Download YouTube audio once per unique video id, transcode to AES-128 HLS, and mirror
the nested layout from input.json with PascalCase folder names.

Requires: yt-dlp, ffmpeg on PATH. Operators must comply with YouTube ToS and content rights.

Single enc.key + keyinfo per asset (no dummy/real dual-key layout from convertAudio.py).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DEFAULT_JSON = HERE / "input.json"

LOG = logging.getLogger("youtube_nested_to_hls")

# --- video id (reuse + live URL fallback) ---------------------------------

try:
    from build_nested_names_youtube import youtube_video_id as _youtube_video_id_base
except ImportError:
    _youtube_video_id_base = None  # type: ignore[misc, assignment]


def youtube_video_id(url: str) -> str | None:
    if _youtube_video_id_base is not None:
        vid = _youtube_video_id_base(url)
        if vid:
            return vid
    m = re.search(r"youtube\.com/live/([a-zA-Z0-9_-]{11})", url)
    if m:
        return m.group(1)
    m = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", url)
    if m:
        return m.group(1)
    m = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", url)
    if m:
        return m.group(1)
    return None


# --- naming ----------------------------------------------------------------

_SPLIT_RE = re.compile(r"[^\w\u0900-\u097F]+", re.UNICODE)


def pascal_folder_name(display_name: str) -> str:
    n = unicodedata.normalize("NFKC", display_name).strip()
    parts = [p for p in _SPLIT_RE.split(n) if p]
    if not parts:
        return "Untitled"
    out: list[str] = []
    for w in parts:
        if len(w) == 1:
            out.append(w.upper())
        else:
            out.append(w[0].upper() + w[1:].lower())
    return "".join(out)


def safe_segment(seg: str) -> str:
    s = unicodedata.normalize("NFKC", seg).strip()
    if ".." in s or "/" in s or "\\" in s:
        raise ValueError(f"unsafe path segment: {seg!r}")
    return s


@dataclass
class Placement:
    top: str
    genre: str
    folder: str
    name: str
    youtube_url: str


@dataclass
class JobIndex:
    """video_id -> placements and a sample URL for download."""

    by_vid: dict[str, dict[str, Any]] = field(default_factory=dict)

    def add(self, vid: str, url: str, placement: Placement) -> None:
        if vid not in self.by_vid:
            self.by_vid[vid] = {"url": url, "placements": []}
        self.by_vid[vid]["placements"].append(placement)


def build_index(data: dict[str, Any]) -> JobIndex:
    idx = JobIndex()
    per_scope: dict[tuple[str, str], dict[str, int]] = {}

    for top, genres in data.items():
        if not isinstance(genres, dict):
            continue
        top_s = safe_segment(str(top))
        for genre, tracks in genres.items():
            if not isinstance(tracks, list):
                continue
            genre_s = safe_segment(str(genre))
            scope = (top_s, genre_s)
            counts = per_scope.setdefault(scope, {})
            for item in tracks:
                if not isinstance(item, dict):
                    continue
                url = (item.get("youtubeUrl") or "").strip()
                name = (item.get("name") or "").strip() or "Untitled"
                if not url:
                    continue
                vid = youtube_video_id(url)
                if not vid:
                    LOG.warning("skip: could not parse video id from %s", url[:80])
                    continue
                base = pascal_folder_name(name)
                n = counts.get(base, 0) + 1
                counts[base] = n
                folder = base if n == 1 else f"{base}_{n}"
                idx.add(
                    vid,
                    url,
                    Placement(
                        top=top_s,
                        genre=genre_s,
                        folder=folder,
                        name=name,
                        youtube_url=url,
                    ),
                )
    return idx


# --- subprocess helpers -----------------------------------------------------

def run_cmd(cmd: list[str], *, cwd: Path | None = None) -> None:
    LOG.debug("run: %s", " ".join(cmd))
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()
        raise RuntimeError(f"command failed ({r.returncode}): {' '.join(cmd)}\n{err}")


def which_or_die(name: str) -> None:
    if not shutil.which(name):
        raise SystemExit(f"required executable not found in PATH: {name}")


def download_audio(url: str, tdir: Path, retries: int = 3) -> Path:
    """Download best audio; return path to media file."""
    tdir.mkdir(parents=True, exist_ok=True)
    template = str(tdir / "%(id)s.%(ext)s")
    last_err: str | None = None
    for attempt in range(1, retries + 1):
        for p in tdir.iterdir():
            if p.is_file():
                p.unlink(missing_ok=True)
        try:
            run_cmd(
                [
                    "yt-dlp",
                    "-f",
                    "bestaudio/best",
                    "--no-playlist",
                    "-o",
                    template,
                    url,
                ]
            )
            matches = [p for p in tdir.iterdir() if p.is_file()]
            if not matches:
                raise RuntimeError("yt-dlp produced no file")
            return max(matches, key=lambda p: p.stat().st_mtime)
        except Exception as e:
            last_err = str(e)
            LOG.warning("download attempt %s/%s failed: %s", attempt, retries, e)
    raise RuntimeError(f"download failed after {retries}: {last_err}")


def write_keyinfo(key_uri: str, key_file: Path, keyinfo_path: Path) -> None:
    # Line1: URI in playlist, Line2: path to key on disk, Line3: empty IV
    keyinfo_path.write_text(
        f"{key_uri}\n{key_file.resolve()}\n\n",
        encoding="utf-8",
    )


def encode_hls(
    src_audio: Path,
    out_dir: Path,
    *,
    encrypt: bool,
    hls_time: int = 6,
    audio_bitrate: str = "128k",
    audio_channels: int = 2,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    playlist = out_dir / "index.m3u8"
    seg_pat = out_dir / "seg_%04d.ts"

    acodec = ["-acodec", "aac", "-b:a", audio_bitrate, "-ac", str(audio_channels)]
    cmd: list[str] = [
        "ffmpeg",
        "-y",
        "-i",
        str(src_audio),
        "-vn",
        *acodec,
        "-f",
        "hls",
        "-hls_time",
        str(hls_time),
        "-hls_playlist_type",
        "vod",
        "-hls_flags",
        "independent_segments",
        "-hls_segment_filename",
        str(seg_pat),
    ]
    if encrypt:
        key_path = out_dir / "enc.key"
        key_path.write_bytes(secrets.token_bytes(16))
        kinfo = out_dir / "enc_keyinfo.txt"
        write_keyinfo("enc.key", key_path, kinfo)
        cmd.extend(["-hls_key_info_file", str(kinfo)])
    cmd.append(str(playlist))
    run_cmd(cmd)


def mirror_canonical_to_placement(canonical: Path, placement_dir: Path) -> None:
    """Hardlink each file from canonical into placement_dir; fallback to copy."""
    placement_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(canonical.iterdir())
    if not files:
        raise RuntimeError(f"empty canonical dir: {canonical}")

    for src in files:
        if not src.is_file():
            continue
        dst = placement_dir / src.name
        if dst.exists():
            continue
        try:
            os.link(src, dst)
        except OSError:
            shutil.copy2(src, dst)


def process_one_video(
    vid: str,
    url: str,
    placements: list[Placement],
    output_root: Path,
    tmp_root: Path,
    *,
    skip_existing: bool,
    encrypt: bool,
) -> None:
    lib = output_root / ".library" / vid
    if skip_existing and (lib / "index.m3u8").is_file():
        LOG.info("[%s] skip encode (exists)", vid)
    else:
        lib.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=tmp_root) as td:
            tdir = Path(td)
            dl = download_audio(url, tdir / "x.bin")
            encode_hls(dl, lib, encrypt=encrypt)
        LOG.info("[%s] encoded HLS -> %s", vid, lib)

    for p in placements:
        dest = output_root / p.top / p.genre / p.folder
        mirror_canonical_to_placement(lib, dest)
        LOG.info("[%s] placement -> %s", vid, dest)


def main() -> int:
    ap = argparse.ArgumentParser(description="YouTube nested JSON to deduped HLS tree.")
    ap.add_argument(
        "--json",
        type=Path,
        default=DEFAULT_JSON,
        help="Path to input.json",
    )
    ap.add_argument(
        "--output-root",
        type=Path,
        default=HERE / "hls_output",
        help="Root folder for .library and mirrored tree",
    )
    ap.add_argument("--workers", type=int, default=1, help="Parallel encodes (default 1)")
    ap.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip download/encode if .library/<id>/index.m3u8 exists",
    )
    ap.add_argument(
        "--no-encrypt",
        action="store_true",
        help="Emit unencrypted HLS (no enc.key / keyinfo)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print unique video ids and placement counts only",
    )
    ap.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Keep processing after a failed video",
    )
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    data = json.loads(args.json.read_text(encoding="utf-8"))
    idx = build_index(data)
    n_vid = len(idx.by_vid)
    n_pl = sum(len(v["placements"]) for v in idx.by_vid.values())
    LOG.info("unique video ids: %s, total placements: %s", n_vid, n_pl)

    if args.dry_run:
        for vid, info in sorted(idx.by_vid.items()):
            print(f"{vid}\t{len(info['placements'])}\t{info['url'][:60]}...")
        return 0

    which_or_die("ffmpeg")
    which_or_die("yt-dlp")

    out = args.output_root.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    tmp_root = out / ".tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)

    encrypt = not args.no_encrypt
    failed: list[str] = []

    def work(item: tuple[str, dict[str, Any]]) -> None:
        vid, info = item
        process_one_video(
            vid,
            info["url"],
            info["placements"],
            out,
            tmp_root,
            skip_existing=args.skip_existing,
            encrypt=encrypt,
        )

    items = list(idx.by_vid.items())
    if args.workers <= 1:
        for it in items:
            try:
                work(it)
            except Exception as e:
                LOG.error("%s", e)
                failed.append(it[0])
                if not args.continue_on_error:
                    raise
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(work, it): it[0] for it in items}
            for fut in as_completed(futs):
                vid = futs[fut]
                try:
                    fut.result()
                except Exception as e:
                    LOG.error("[%s] %s", vid, e)
                    failed.append(vid)
                    if not args.continue_on_error:
                        raise

    if failed:
        LOG.error("failed video ids: %s", ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
