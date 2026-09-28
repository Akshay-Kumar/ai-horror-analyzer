import json
from pathlib import Path
from .schemas import HorrorScores

DIMENSIONS = list(HorrorScores.model_fields.keys())


def load_weights(path: str = "config/scoring.json"):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["weights"]


def weighted_score(scores: HorrorScores, weights: dict) -> float:
    available = {
        d: getattr(scores, d)
        for d in DIMENSIONS
        if getattr(scores, d) is not None and weights.get(d, 0) > 0
    }
    if not available:
        return 0.0
    total = sum(available[d] * weights.get(d, 0) for d in available)
    used = sum(weights.get(d, 0) for d in available)
    return round(total / used, 2) if used else 0.0


def average_scores(items) -> HorrorScores:
    if not items:
        return HorrorScores()
    values = {}
    for d in DIMENSIONS:
        observed = [getattr(x, d) for x in items if getattr(x, d) is not None]
        values[d] = round(sum(observed) / len(observed), 2) if observed else None
    return HorrorScores(**values)
