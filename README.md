# AI Horror Analyzer V2

Content-based horror analysis for movies and TV episodes. It does not use public reviews or ratings.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add `OPENAI_API_KEY` to `.env`.

## Test Annabelle with 3 segments

With 2-minute segments, analyze segments 0, 20 and 40:

```bash
python main.py "input/Annabelle (2014) Bluray-1080p.mkv" --segments 0,20,40
```

This extracts 9 frames and makes 3 multimodal analysis requests.

## Whole movie

```bash
python main.py "input/movie.mkv"
```

## Output

```text
output/<movie-name>/frames/
output/<movie-name>/analysis.json
```

The JSON keeps segment-level scores, explanations, fear mechanisms and confidence.

The 1–10 number is an experimental **content-based horror effectiveness** score, not an objective measure of how frightening every viewer will find the movie.
