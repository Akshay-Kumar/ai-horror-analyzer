import json
import shutil
import subprocess
from pathlib import Path
from .schemas import MediaInfo

def require_binary(name: str):
    if shutil.which(name) is None:
        raise RuntimeError(f"{name} was not found on PATH. Install FFmpeg and ensure {name} is available.")

def probe_media(path: Path) -> MediaInfo:
    require_binary("ffprobe")
    cmd = ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    fmt = data.get("format", {})
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    return MediaInfo(path=str(path.resolve()), filename=path.name, duration_seconds=float(fmt.get("duration", 0)), width=video.get("width") if video else None, height=video.get("height") if video else None, video_codec=video.get("codec_name") if video else None, audio_streams=sum(s.get("codec_type") == "audio" for s in streams), subtitle_streams=sum(s.get("codec_type") == "subtitle" for s in streams))

def extract_frame(video: Path, timestamp: float, output: Path):
    require_binary("ffmpeg")
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-ss", f"{timestamp:.3f}", "-i", str(video), "-frames:v", "1", "-q:v", "3", str(output)]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def build_segments(video: Path, duration: float, output_dir: Path, segment_seconds: int = 120, frames_per_segment: int = 3, selected_indices: list[int] | None = None):
    segments = []
    frame_dir = output_dir / "frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    if duration <= 0:
        return segments
    total_segments = (int(duration) + segment_seconds - 1) // segment_seconds
    indices = list(range(total_segments)) if selected_indices is None else sorted(set(selected_indices))
    for index in indices:
        if index < 0 or index >= total_segments:
            print(f"Warning: segment {index} is outside the movie; skipping.")
            continue
        start = index * segment_seconds
        end = min(start + segment_seconds, duration)
        span = end - start
        frames = []
        for n in range(frames_per_segment):
            timestamp = start + span * ((n + 1) / (frames_per_segment + 1))
            frame_path = frame_dir / f"segment_{index:04d}_frame_{n:02d}.jpg"
            extract_frame(video, timestamp, frame_path)
            frames.append(str(frame_path))
        segments.append({"index": index, "start_seconds": start, "end_seconds": end, "frame_paths": frames, "dialogue": ""})
    return segments
