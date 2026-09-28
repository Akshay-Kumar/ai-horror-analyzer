import json
import subprocess
from pathlib import Path
from .schemas import MediaInfo, Segment


def probe_media(path: str) -> MediaInfo:
    cmd = [
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_streams", "-show_format", path
    ]
    data = json.loads(subprocess.check_output(cmd, text=True))
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio_count = sum(s.get("codec_type") == "audio" for s in streams)
    subtitle_count = sum(s.get("codec_type") == "subtitle" for s in streams)
    duration = float(data.get("format", {}).get("duration") or 0)
    return MediaInfo(
        path=str(path),
        filename=Path(path).name,
        duration_seconds=duration,
        width=int(video.get("width") or 0),
        height=int(video.get("height") or 0),
        video_codec=video.get("codec_name"),
        audio_streams=audio_count,
        subtitle_streams=subtitle_count,
    )


def extract_frame(media_path: str, timestamp: float, output_path: str) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-ss", f"{max(0, timestamp):.3f}", "-i", media_path,
        "-frames:v", "1", "-q:v", "3", output_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path


def build_segments(media: MediaInfo, output_dir: str, segment_seconds: int = 120,
                   frames_per_segment: int = 3, selected_indices: set[int] | None = None):
    out = Path(output_dir)
    segments = []
    total = media.duration_seconds
    index = 0
    while index * segment_seconds < total:
        if selected_indices is not None and index not in selected_indices:
            index += 1
            continue
        start = index * segment_seconds
        end = min(start + segment_seconds, total)
        length = max(0.1, end - start)
        if frames_per_segment == 1:
            offsets = [length / 2]
        else:
            offsets = [length * (i + 1) / (frames_per_segment + 1) for i in range(frames_per_segment)]
        frame_paths = []
        for frame_no, offset in enumerate(offsets):
            ts = start + offset
            frame_path = out / f"segment_{index:04d}" / f"frame_{frame_no:02d}.jpg"
            frame_paths.append(extract_frame(media.path, ts, str(frame_path)))
        segments.append(Segment(index=index, start_seconds=start, end_seconds=end, frame_paths=frame_paths))
        index += 1
    return segments
