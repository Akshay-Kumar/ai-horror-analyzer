from pathlib import Path
import subprocess
import json


def probe_media(path: str) -> dict:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries",
        "format=duration:stream=index,codec_type,codec_name,width,height",
        "-of", "json", path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)

    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    return {
        "path": str(Path(path).resolve()),
        "duration_seconds": float(data.get("format", {}).get("duration", 0) or 0),
        "width": video.get("width"),
        "height": video.get("height"),
        "video_codec": video.get("codec_name"),
        "audio_streams": sum(1 for s in streams if s.get("codec_type") == "audio"),
        "subtitle_streams": sum(1 for s in streams if s.get("codec_type") == "subtitle"),
    }


def extract_frames(media_path: str, start: float, end: float, out_dir: str, count: int = 3) -> list[str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    duration = max(0.1, end - start)
    paths = []

    for i in range(count):
        # Avoid exact segment boundaries.
        offset = start + duration * ((i + 1) / (count + 1))
        frame_path = out / f"frame_{i:02d}.jpg"

        cmd = [
            "ffmpeg", "-y", "-ss", f"{offset:.3f}", "-i", media_path,
            "-frames:v", "1", "-q:v", "3", str(frame_path)
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        paths.append(str(frame_path))

    return paths


def build_segments(duration: float, segment_seconds: int, out_root: str, media_path: str, sample_indices=None):
    total = int((duration + segment_seconds - 1) // segment_seconds)
    indices = list(range(total)) if sample_indices is None else sample_indices

    segments = []
    for idx in indices:
        start = idx * segment_seconds
        end = min(duration, start + segment_seconds)
        frame_dir = Path(out_root) / f"segment_{idx:04d}"
        frames = extract_frames(media_path, start, end, str(frame_dir))
        segments.append({
            "index": idx,
            "start": start,
            "end": end,
            "frame_paths": frames,
        })
    return segments, total
