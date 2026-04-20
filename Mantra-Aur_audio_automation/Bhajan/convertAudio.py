#!/usr/bin/env python3
"""
Convert & Encrypt MP3 Audio to HLS (TS) for Durlabh Darshan style pipeline.

- Input:  .mp3 (or a folder containing .mp3 files)
- Output: /output_root/<audio_name>/index.m3u8 + segments
- Encryption: AES-128 via FFmpeg using a keyinfo file
- Dummy key file: encrypt_key.key (safe to upload / intercepted by AVPro)
- Real key bytes: stored locally, DO NOT UPLOAD

Requires: ffmpeg in PATH
"""

import os
import shlex
import subprocess
import secrets
import binascii
import argparse
from pathlib import Path

# ---------------- CONFIG ---------------- #

CONFIG = {
    # Default output root folder (can override via CLI)
    "OUTPUT_ROOT": "output_audio_hls",

    # HLS options
    "HLS_SEGMENT_DURATION": 6,        # seconds
    "HLS_PLAYLIST_TYPE": "vod",       # "vod" or "event"

    # Audio encoding options
    "AUDIO_BITRATE": "128k",          # e.g. "128k", "192k"
    "AUDIO_CHANNELS": 2,              # 1 or 2

    # Enc key handling
    "KEY_URI_IN_PLAYLIST": "encrypt_key.key",  # appears in playlist
    "REAL_KEY_HEX_FILENAME": "real_key_hex.txt",
    "REAL_KEY_BIN_FILENAME": "real_key.bin",
    "KEYINFO_FILENAME": "enc_keyinfo.txt",
    "DUMMY_KEY_FILENAME": "encrypt_key.key",
}

# -------------- UTILITIES --------------- #

def run(cmd: str):
    """Run a shell command and stream output."""
    print(f"\n[ffmpeg] {cmd}\n")
    proc = subprocess.run(cmd, shell=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed with code {proc.returncode}: {cmd}")

def generate_real_key(hex_path: Path, bin_path: Path) -> bytes:
    """
    Generate a 16-byte AES-128 key.
    - Save hex (for humans) in hex_path
    - Save raw bytes in bin_path
    """
    key = secrets.token_bytes(16)
    key_hex = binascii.hexlify(key).decode("ascii")

    hex_path.write_text(key_hex, encoding="utf-8")
    with bin_path.open("wb") as f:
        f.write(key)

    print(f"✓ Wrote REAL key (hex): {hex_path}")
    print(f"✓ Wrote REAL key (bin): {bin_path}")
    return key

def make_keyinfo(
    keyinfo_path: Path,
    key_uri_in_playlist: str,
    local_real_key_bin_path: Path,
    iv_hex: str | None = None,
):
    """
    Create FFmpeg keyinfo file:
      Line 1: URI that appears in playlist (dummy placeholder)
      Line 2: Local path to REAL key bytes
      Line 3: IV (optional) – if omitted, FFmpeg uses per-segment IVs
    """
    if iv_hex:
        text = f"{key_uri_in_playlist}\n{local_real_key_bin_path}\n{iv_hex}\n"
    else:
        text = f"{key_uri_in_playlist}\n{local_real_key_bin_path}\n"
    keyinfo_path.write_text(text, encoding="utf-8")
    print(f"✓ Wrote keyinfo: {keyinfo_path}")

def write_dummy_key(dummy_key_path: Path):
    """
    Create a dummy key file (non-empty) next to the playlist.
    This is what goes to CDN / S3; AVPro will intercept and swap.
    """
    if not dummy_key_path.exists():
        dummy_key_path.write_text("x", encoding="utf-8")   # 1 byte
        print(f"✓ Wrote dummy key: {dummy_key_path}")
    else:
        print(f"• Dummy key already exists: {dummy_key_path}")

# -------------- CORE LOGIC -------------- #

def pack_audio_to_hls(src: Path, out_dir: Path):
    """
    Convert single MP3 to encrypted HLS inside out_dir.
    Produces:
      - index.m3u8
      - audio_seg_0001.ts ...
      - real_key_hex.txt
      - real_key.bin
      - encrypt_key.key (dummy)
      - enc_keyinfo.txt
    """
    print(f"\n=== Processing audio: {src.name} ===")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Paths
    real_hex_path = out_dir / CONFIG["REAL_KEY_HEX_FILENAME"]
    real_bin_path = out_dir / CONFIG["REAL_KEY_BIN_FILENAME"]
    keyinfo_path = out_dir / CONFIG["KEYINFO_FILENAME"]
    dummy_key_path = out_dir / CONFIG["DUMMY_KEY_FILENAME"]

    playlist_path = out_dir / "index.m3u8"
    segments_pattern = out_dir / "audio_seg_%04d.ts"

    # Generate real key
    _ = generate_real_key(real_hex_path, real_bin_path)

    # Create keyinfo for ffmpeg
    make_keyinfo(
        keyinfo_path,
        CONFIG["KEY_URI_IN_PLAYLIST"],
        real_bin_path,
        iv_hex=None,  # per-segment IVs
    )

    # Dummy key (this is what will be uploaded)
    write_dummy_key(dummy_key_path)

    # FFmpeg HLS command (audio-only)
    seg_sec = CONFIG["HLS_SEGMENT_DURATION"]
    playlist_type = CONFIG["HLS_PLAYLIST_TYPE"]
    abitrate = CONFIG["AUDIO_BITRATE"]
    ach = CONFIG["AUDIO_CHANNELS"]

    cmd = (
        f'ffmpeg -y -i {shlex.quote(str(src))} '
        f'-vn '  # no video
        f'-acodec aac -b:a {abitrate} -ac {ach} '
        f'-f hls '
        f'-hls_time {seg_sec} '
        f'-hls_playlist_type {playlist_type} '
        f'-hls_flags independent_segments '
        f'-hls_segment_filename {shlex.quote(str(segments_pattern))} '
        f'-hls_key_info_file {shlex.quote(str(keyinfo_path))} '
        f'{shlex.quote(str(playlist_path))}'
    )

    run(cmd)

    print("\n--- OUTPUT ---")
    print(f"Audio folder         : {out_dir}")
    print(f"Variant playlist     : {playlist_path}")
    print(f"Real enc key (hex)   : {real_hex_path}   [KEEP PRIVATE]")
    print(f"Real enc key (bin)   : {real_bin_path}   [KEEP PRIVATE]")
    print(f"Dummy key to upload  : {dummy_key_path}")
    print("Upload index.m3u8 + *.ts + encrypt_key.key to CDN/S3")
    print("Do NOT upload real_key_hex.txt or real_key.bin\n")

def is_audio_file(p: Path) -> bool:
    return p.suffix.lower() in {".mp3", ".wav", ".m4a", ".aac"}

def process_input(input_path: Path, output_root: Path):
    """
    If input is a file: process that file.
    If input is a directory: process all *.mp3 (and a few other audio formats).
    """
    if input_path.is_file():
        if not is_audio_file(input_path):
            raise ValueError(f"Input file is not a supported audio type: {input_path}")
        out_dir = output_root / input_path.stem
        pack_audio_to_hls(input_path, out_dir)
    elif input_path.is_dir():
        audio_files = sorted([p for p in input_path.iterdir() if is_audio_file(p)])
        if not audio_files:
            print(f"No audio files found in: {input_path}")
            return
        print(f"Found {len(audio_files)} audio file(s) in {input_path}")
        for af in audio_files:
            out_dir = output_root / af.stem
            pack_audio_to_hls(af, out_dir)
    else:
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

# -------------- CLI ENTRYPOINT ---------- #

def main():
    parser = argparse.ArgumentParser(
        description="Convert & encrypt MP3 audio to HLS (m3u8) with AES-128."
    )
    parser.add_argument(
        "input",
        help="Input .mp3 file OR folder containing .mp3 files"
    )
    parser.add_argument(
        "-o",
        "--output-root",
        default=CONFIG["OUTPUT_ROOT"],
        help=f"Root output folder (default: {CONFIG['OUTPUT_ROOT']})"
    )
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_root = Path(args.output_root).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    print(f"Input       : {input_path}")
    print(f"Output root : {output_root}")

    process_input(input_path, output_root)

if __name__ == "__main__":
    main()
