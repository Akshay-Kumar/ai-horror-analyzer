# AI Horror Analyzer — Ollama V3

Local multimodal horror analysis using Ollama + Qwen3-VL. No OpenAI API credits are required.

## Setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Make sure Ollama is running and the model is installed:

```powershell
ollama pull qwen3-vl:8b
```

## Test a few segments

```powershell
python main.py "input\Annabelle (2014) Bluray-1080p.mkv" --segments 0,20,40
```

The analyzer uses an 8192-token context by default. Override it with `--num-ctx` if needed.

### Important

A run with `--segments 0,20,40` is a **sample**, not a full-movie score. The JSON records the sampled coverage percentage. Do not treat the sampled score as the final movie score until the movie has sufficient segment coverage.

The model is instructed to return `null` for dimensions that cannot be supported by the supplied still frames. This prevents unsupported guesses from contaminating the movie-level averages.
