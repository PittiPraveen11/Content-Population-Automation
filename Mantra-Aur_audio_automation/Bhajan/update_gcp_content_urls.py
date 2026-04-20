#!/usr/bin/env python3
"""Sync target JSON contentUrl from a canonical reference JSON by video id.

Use case:
- Reference file has correct streamingOptions[*].contentUrl values.
- Target file may contain outdated/alternate contentUrl paths.

Only streamingOptions[*].contentUrl is mutated.
"""

from __future__ import annotations

import argparse
import json
from urllib.parse import urlparse
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
GCP_DIR = HERE / "gcpLinks"
DEFAULT_REFERENCE = GCP_DIR / "cleandataDTO copy.json"
DEFAULT_TARGET = GCP_DIR / "BajanAudio.json"

def folder_slug_from_url(url: str) -> str | None:
    try:
        parsed = urlparse(url)
    except Exception:
        return None
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        return None
    if parts[-1].lower() != "index.m3u8":
        return None
    return parts[-2]


def walk_collect_reference(
    node: Any,
    by_folder: dict[str, str],
    conflicts: dict[str, set[str]],
) -> None:
    if isinstance(node, dict):
        opts = node.get("streamingOptions")
        if isinstance(opts, list):
            for i, opt in enumerate(opts):
                if not isinstance(opt, dict):
                    continue
                cur = opt.get("contentUrl")
                if not isinstance(cur, str):
                    continue
                folder = folder_slug_from_url(cur)
                if not folder:
                    continue
                prev = by_folder.get(folder)
                if prev is None:
                    by_folder[folder] = cur
                elif prev != cur:
                    conflicts.setdefault(folder, set()).update({prev, cur})
        for k, v in node.items():
            walk_collect_reference(v, by_folder, conflicts)
    elif isinstance(node, list):
        for item in node:
            walk_collect_reference(item, by_folder, conflicts)


def walk_replace_target(
    node: Any,
    by_folder: dict[str, str],
    stats: dict[str, int],
    unmatched_keys: set[str],
) -> None:
    if isinstance(node, dict):
        opts = node.get("streamingOptions")
        if isinstance(opts, list):
            for i, opt in enumerate(opts):
                if not isinstance(opt, dict):
                    continue
                cur = opt.get("contentUrl")
                if not isinstance(cur, str):
                    continue
                stats["total_seen"] += 1
                folder = folder_slug_from_url(cur) or "(no-folder-slug)"
                expected = by_folder.get(folder)
                if not expected:
                    stats["unmatched"] += 1
                    unmatched_keys.add(folder)
                    continue
                if cur == expected:
                    stats["already_correct"] += 1
                else:
                    opt["contentUrl"] = expected
                    stats["replaced"] += 1
        for _k, v in node.items():
            walk_replace_target(v, by_folder, stats, unmatched_keys)
    elif isinstance(node, list):
        for item in node:
            walk_replace_target(item, by_folder, stats, unmatched_keys)


def _all_paths_except_content_url(node: Any, prefix: str = "$") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(node, dict):
        for k, v in node.items():
            p = f"{prefix}.{k}"
            if k == "contentUrl":
                continue
            out.update(_all_paths_except_content_url(v, p))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out.update(_all_paths_except_content_url(v, f"{prefix}[{i}]"))
    else:
        out[prefix] = node
    return out


def process_target(
    target_path: Path, by_folder: dict[str, str], write: bool
) -> tuple[dict[str, int], list[str]]:
    original = json.loads(target_path.read_text(encoding="utf-8"))
    mutated = json.loads(target_path.read_text(encoding="utf-8"))
    stats = {"total_seen": 0, "replaced": 0, "already_correct": 0, "unmatched": 0}
    unmatched_keys: set[str] = set()
    walk_replace_target(mutated, by_folder, stats, unmatched_keys)

    # Safety: verify only contentUrl changed.
    before_non_url = _all_paths_except_content_url(original)
    after_non_url = _all_paths_except_content_url(mutated)
    if before_non_url != after_non_url:
        raise RuntimeError(
            f"Safety check failed for {target_path.name}: non-contentUrl fields changed."
        )

    if write:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        bak = target_path.with_suffix(target_path.suffix + f".{ts}.bak")
        shutil.copy2(target_path, bak)
        target_path.write_text(
            json.dumps(mutated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"backup={bak}")
    return stats, sorted(unmatched_keys)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Sync target contentUrl values from reference JSON by video id."
    )
    ap.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    ap.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    ap.add_argument("--write", action="store_true", help="Write files; default is dry-run.")
    args = ap.parse_args()

    ref_data = json.loads(args.reference.read_text(encoding="utf-8"))
    ref_by_folder: dict[str, str] = {}
    conflicts: dict[str, set[str]] = {}
    walk_collect_reference(ref_data, ref_by_folder, conflicts)
    print(f"reference_folder_keys={len(ref_by_folder)}")
    if not ref_by_folder:
        raise SystemExit("No reference folder keys found. Aborting.")
    if conflicts:
        print(f"reference_conflicting_folder_keys={len(conflicts)}")
        for folder in sorted(conflicts):
            vals = sorted(conflicts[folder])
            print(f"reference_conflict: {folder} -> {' || '.join(vals)}")

    s, unmatched = process_target(args.target, ref_by_folder, write=args.write)
    print(
        f"{args.target.name}: total_seen={s['total_seen']} replaced={s['replaced']} "
        f"already_correct={s['already_correct']} unmatched={s['unmatched']}"
    )
    if unmatched:
        print(f"{args.target.name}: unmatched_folder_slugs={','.join(unmatched)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

