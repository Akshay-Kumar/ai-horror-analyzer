# AI Horror Analyzer — V2 Local Vision

Local multimodal horror analysis using **Ollama + Qwen3-VL 8B**. No OpenAI API credits are required.

Qwen3-VL 8B supports image input and Ollama supports structured JSON output using a Pydantic/JSON schema. The local Ollama API is used at `http://127.0.0.1:11434`.

## Requirements

- Windows 10/11
- Python 3.10+
- FFmpeg + ffprobe on PATH
- Ollama installed and running
- `qwen3-vl:8b` pulled
- NVIDIA GPU recommended; this project was tested conceptually around an RTX 4070 Ti + 12 GB VRAM

## Setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Verify Ollama:

```powershell
ollama list
ollama run qwen3-vl:8b
```

## First test

Use only three segments first:

```powershell
python main.py "input\Annabelle (2014) Bluray-1080p.mkv" --segments 0,20,40
```

Each selected two-minute segment uses three chronological frames. The model analyzes the frames together so it can identify visual progression, not just isolated images.

Output:

```text
output\Annabelle (2014) Bluray-1080p\analysis.json
output\Annabelle (2014) Bluray-1080p\frames\...
```

## Full movie

Only run this after reviewing the 3-segment test:

```powershell
python main.py "input\Annabelle (2014) Bluray-1080p.mkv"
```

A 97-minute movie at 120-second segments is roughly 49 segments / 147 frames.

## Architecture

```text
Movie
  -> FFmpeg
  -> representative frames
  -> Qwen3-VL 8B via local Ollama
  -> structured scene observations
  -> ten horror dimensions
  -> weighted score
  -> analysis.json
```

## Important limitation

The model is analyzing evidence in the supplied frames. It is not claiming to feel fear and it does not use public ratings/reviews. Temporal dimensions such as pacing and shock are scored conservatively because only three sampled frames are supplied for each two-minute segment.

Next iterations can add subtitle extraction, scene-change detection, audio features, better temporal aggregation, and Plex integration.
