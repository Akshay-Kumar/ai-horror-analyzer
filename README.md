# AI Horror Analyzer V5.1

Local, review-independent horror analysis using a two-stage Ollama pipeline.

## Architecture

1. **Qwen3-VL 8B** receives representative movie frames.
2. It produces visual evidence/reasoning only.
3. **Qwen3 4B** receives that evidence and produces strict Pydantic-compatible JSON.
4. Python validates the JSON and calculates the weighted segment score.
5. The final JSON keeps segment-level evidence and dimension scores.

This design avoids relying on Qwen3-VL's final `content` field, which can be empty when
the model puts its response into the thinking channel.

## Requirements

- Windows 11
- FFmpeg + ffprobe on PATH
- Ollama
- Qwen3-VL 8B
- Qwen3 4B
- Python 3.10+

Install:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

ollama pull qwen3-vl:8b
ollama pull qwen3:4b
```

## Quick test

Use three evenly distributed segments:

```powershell
python main.py "C:\path	o\movie.mkv" --segments 3
```

Output:

```text
output/analysis.json
```

## Full movie

After the 3-segment test succeeds:

```powershell
python main.py "C:\path	o\movie.mkv"
```

For a ~100-minute movie with 2-minute segments this is roughly 50 segments.

## GPU/RAM note

The vision model uses the RTX GPU. The text model is configured with
`num_gpu=0`, so the 4B text model runs on CPU/RAM and does not compete with the
vision model for the 12 GB GPU.

## Scoring

The configured dimensions are:

- dread
- suspense
- uncertainty
- vulnerability
- psychological
- atmosphere
- threat
- shock
- disturbance
- pacing

Each dimension can be `null` when still-frame evidence is insufficient. Confidence is
capped at 0.8. The weighted segment score uses score × confidence so weak evidence has
less influence.

Weights are editable in:

```text
config/scoring.json
```

## Important limitation

V5 is intentionally conservative. With only three still frames per two-minute
segment, temporal properties such as jump scares, pacing, escalation, and sustained
suspense cannot be measured reliably. V6 should add subtitles, audio features,
shot boundaries, and short temporal frame sequences.

## V5.1 fix

The vision request now uses Ollama's native `/api/chat` multimodal format:
`content` is a normal string and the images are supplied through the message's
`images` array as base64 JPEG data. This fixes the HTTP 400 caused by sending
OpenAI-style `image_url` content blocks to Ollama.
