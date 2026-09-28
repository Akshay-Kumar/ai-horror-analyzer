import json
from pathlib import Path
from statistics import mean
from .schemas import DIMENSIONS, HorrorScores, SegmentAnalysis

def load_weights(path: Path):
    weights = json.loads(path.read_text(encoding="utf-8"))["weights"]
    if set(weights) != set(DIMENSIONS):
        raise ValueError("Scoring dimensions and configured weights do not match.")
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"Scoring weights must sum to 1.0; got {total}")
    return weights

def weighted_score(scores: HorrorScores, weights):
    return round(sum(getattr(scores, d) * w for d, w in weights.items()), 2)

def aggregate(segment_analyses: list[SegmentAnalysis]):
    if not segment_analyses:
        return HorrorScores(**{d: 0 for d in DIMENSIONS})
    values = {d: mean(getattr(item.scores, d) for item in segment_analyses) for d in DIMENSIONS}
    return HorrorScores(**{k: round(v, 2) for k, v in values.items()})
