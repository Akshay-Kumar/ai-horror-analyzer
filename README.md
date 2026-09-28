# AI Horror Analyzer — V1

A local, modular proof-of-concept for analyzing movies/TV episodes for horror effectiveness.

## V1 pipeline

```text
Movie file
   ↓
FFprobe / FFmpeg
   ↓
Media metadata
   ↓
Time segments
   ↓
Representative frames
   ↓
AI analyzer interface
   ↓
Scene-level horror dimensions
   ↓
Weighted 1–10 score
   ↓
analysis.json
```

## Requirements

- Python 3.10+
- FFmpeg + ffprobe available on PATH

Check:

```bash
ffmpeg -version
ffprobe -version
```

Python packages:

```bash
pip install -r requirements.txt
```

## First run

Put a movie in `input/`, for example:

```text
input/movie.mkv
```

Then:

```bash
python main.py input/movie.mkv
```

V1 currently creates the media/segment/frame analysis package and uses a deterministic placeholder analyzer. This is intentional: we will add the real multimodal AI analyzer after validating extraction.

Output:

```text
output/<movie-name>/analysis.json
output/<movie-name>/frames/
```

## Next milestones

1. Real multimodal AI analysis
2. Subtitle extraction / transcription
3. Scene-change detection
4. Audio features
5. Database persistence
6. React dashboard
7. Plex integration
