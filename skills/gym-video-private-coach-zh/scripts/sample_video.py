#!/usr/bin/env python3
"""Extract local review frames; does not detect exercises, repetitions, or pose."""

import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys


def positive(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be a finite number > 0")
    return number


def nonnegative(value):
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError("must be a finite number >= 0")
    return number


def run(command):
    return subprocess.run(
        command, check=True, capture_output=True, text=True, timeout=120
    ).stdout


def sample(args):
    for executable in ("ffprobe", "ffmpeg"):
        if shutil.which(executable) is None:
            raise ValueError(f"{executable} is required; install FFmpeg first")
    source = args.video.expanduser().resolve(strict=True)
    if not source.is_file():
        raise ValueError("input must be a local video file")
    if args.max_frames < 1 or args.max_frames > 200:
        raise ValueError("--max-frames must be between 1 and 200")
    metadata = json.loads(run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,avg_frame_rate,duration:format=duration",
        "-of", "json", str(source),
    ]))
    streams = metadata.get("streams", [])
    if not streams:
        raise ValueError("input has no video stream")
    stream = streams[0]
    raw_duration = stream.get("duration")
    if raw_duration in (None, "N/A"):
        raw_duration = metadata.get("format", {}).get("duration")
    try:
        duration = float(raw_duration)
    except (ValueError, TypeError):
        raise ValueError("cannot determine video duration") from None
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("video duration must be finite and positive")
    end = duration if args.end is None else args.end
    if not 0 <= args.start < end <= duration:
        raise ValueError(f"require 0 <= start < end <= duration ({duration:.6f}s)")
    requested = (end - args.start) / args.every
    if not math.isfinite(requested):
        raise ValueError("sampling interval is too small")
    count = math.ceil(requested)
    if count > args.max_frames:
        raise ValueError(
            f"requested {count} frames, limit is {args.max_frames}; "
            "increase --every or narrow --start/--end (no silent subsampling)"
        )
    output = args.out.expanduser().resolve()
    # A fresh directory prevents mixing stale frames or overwriting earlier work.
    output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "schema_version": 1,
        "source_name": source.name,
        "duration_seconds": duration,
        "encoded_width": stream.get("width"),
        "encoded_height": stream.get("height"),
        "reported_average_frame_rate": stream.get("avg_frame_rate"),
        "range_seconds": [args.start, end],
        "every_seconds": args.every,
        "note": "Seek times are approximate source offsets, not exact frame PTS. "
                "FFmpeg autorotation is enabled. No exercise or rep analysis performed.",
        "status": "extracting",
        "frames": [],
        "skipped_requests": [],
    }
    manifest_path = output / "manifest.json"

    def save():
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    save()
    try:
        for index in range(count):
            seconds = args.start + index * args.every
            if seconds >= end:
                break
            name = f"frame_{index + 1:04d}.jpg"
            target = output / name
            run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-n",
                "-ss", f"{seconds:.9f}", "-i", str(source),
                "-map", "0:v:0", "-frames:v", "1", "-an",
                "-vf", "scale=w='min(1280,iw)':h=-2", "-pix_fmt", "yuvj420p", "-q:v", "3",
                "-map_metadata", "-1", str(target),
            ])
            if not target.is_file() or target.stat().st_size == 0:
                # Container duration can extend past the last decodable frame.
                # Disclose the final request instead of fabricating a frame.
                if end == duration and seconds + args.every >= end and manifest["frames"]:
                    manifest["skipped_requests"].append({
                        "requested_source_seconds": round(seconds, 9),
                        "reason": "no frame decoded after seek near source end",
                    })
                    save()
                    continue
                raise ValueError(f"no frame decoded near {seconds:.6f}s")
            manifest["frames"].append({
                "file": name, "requested_source_seconds": round(seconds, 9)
            })
            save()
    except Exception:
        manifest["status"] = "incomplete"
        save()
        raise
    manifest["status"] = "complete"
    save()
    print(f"Extracted {len(manifest['frames'])} frames, "
          f"{len(manifest['skipped_requests'])} skipped tail requests: {manifest_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--out", required=True, type=Path, help="new private output directory")
    parser.add_argument("--start", type=nonnegative, default=0.0, help="seconds from source start")
    parser.add_argument("--end", type=positive, help="exclusive source end in seconds")
    parser.add_argument("--every", type=positive, default=2.0, help="sampling interval in seconds")
    parser.add_argument("--max-frames", type=int, default=48, help="hard cap, at most 200")
    args = parser.parse_args()
    try:
        sample(args)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        message = error.stderr.strip() if isinstance(error, subprocess.CalledProcessError) else str(error)
        print(f"Error: {message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
