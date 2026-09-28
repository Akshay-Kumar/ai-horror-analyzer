import json
from pathlib import Path
from .schemas import HorrorScores

DIMENSIONS = list(HorrorScores.model_fields.keys())


def load_weights(path: str = "config/scoring.json"):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["weights"]


def weighted_score(scores: HorrorScores, weights: dict) -> float:
    total = sum(getattr(scores, d) * weights.get(d, 0) for d in DIMENSIONS)
    used = sum(weights.get(d, 0) for d in DIMENSIONS)
    return round(total / used, 2) if used else 0.0


def average_scores(items) -> HorrorScores:
    if not items:
        return HorrorScores(**{d: 0 for d in DIMENSIONS})
    return HorrorScores(**{
        d: round(sum(getattr(x, d) for x in items) / len(items), 2)
        for d in DIMENSIONS
    })
