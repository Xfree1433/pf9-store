"""
Stitch screenshots + ElevenLabs voiceover into a marketing video.

The Cowork Creative agent generates the voiceover via ElevenLabs and
pulls real product screenshots from ./screenshots/. This script
composes them into an MP4 using ffmpeg.

Setup (one time):
    Install ffmpeg:  apt install ffmpeg  (or brew install ffmpeg)

Run:
    python tools/compose_video.py \\
        --voiceover audio/flowtrack_pitch.mp3 \\
        --shots flowtrack_default_20260101.png shiftlog_default_20260101.png \\
        --shot-duration 4.0 \\
        --output marketing/flowtrack_pitch.mp4

Notes:
- Each shot displays for --shot-duration seconds (default 4.0).
- Total video length is max(sum of shot durations, voiceover length).
- Shots are letterboxed/scaled to 1920x1080 by default; pass
  --resolution 1080x1920 for vertical (TikTok/Reels/Shorts).
- Output is H.264 + AAC, broadly compatible.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def check_ffmpeg():
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH. Install: apt install ffmpeg / brew install ffmpeg")


def ffprobe_duration(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ])
    return float(out.strip())


def build_concat_list(shots, durations, tmpdir):
    list_path = Path(tmpdir) / "concat.txt"
    with open(list_path, "w") as f:
        for shot, dur in zip(shots, durations):
            f.write(f"file '{Path(shot).resolve()}'\n")
            f.write(f"duration {dur}\n")
        f.write(f"file '{Path(shots[-1]).resolve()}'\n")
    return list_path


def main():
    parser = argparse.ArgumentParser(description="Compose voiceover + screenshots into MP4")
    parser.add_argument("--voiceover", required=True, help="Audio file (mp3/wav)")
    parser.add_argument("--shots", required=True, nargs="+", help="Screenshot files in display order")
    parser.add_argument("--shot-duration", type=float, default=4.0, help="Seconds per shot")
    parser.add_argument("--resolution", default="1920x1080", help="Output resolution WxH")
    parser.add_argument("--output", required=True, help="Output mp4 path")
    args = parser.parse_args()

    check_ffmpeg()

    voiceover = Path(args.voiceover)
    if not voiceover.exists():
        sys.exit(f"voiceover not found: {voiceover}")

    for shot in args.shots:
        if not Path(shot).exists():
            sys.exit(f"shot not found: {shot}")

    width, height = args.resolution.split("x")
    audio_dur = ffprobe_duration(voiceover)
    visual_dur = args.shot_duration * len(args.shots)

    if audio_dur > visual_dur:
        per_shot = audio_dur / len(args.shots)
        durations = [per_shot] * len(args.shots)
        print(f"audio ({audio_dur:.1f}s) longer than visuals — stretching shots to {per_shot:.2f}s each")
    else:
        durations = [args.shot_duration] * len(args.shots)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        concat_list = build_concat_list(args.shots, durations, tmpdir)

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_list),
            "-i", str(voiceover),
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,format=yuv420p",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest" if audio_dur < visual_dur else "-t", str(max(audio_dur, visual_dur)),
            str(output_path),
        ]

        print(f"composing {output_path} ({args.resolution}, {len(args.shots)} shots, {max(audio_dur, visual_dur):.1f}s)")
        subprocess.run(cmd, check=True)

    print(f"done: {output_path}")


if __name__ == "__main__":
    main()
