from .schemas import DIMENSIONS

DEFAULT_WEIGHTS = {
    "dread": 0.15,
    "suspense": 0.15,
    "uncertainty": 0.10,
    "vulnerability": 0.10,
    "psychological": 0.15,
    "atmosphere": 0.10,
    "threat": 0.10,
    "shock": 0.05,
    "disturbance": 0.05,
    "pacing": 0.05,
}


def weighted_score(analysis, weights=None):
    weights = weights or DEFAULT_WEIGHTS
    numerator = 0.0
    denominator = 0.0
    used = {}

    for dim in DIMENSIONS:
        item = getattr(analysis, dim)
        if item.score is None:
            continue
        weight = float(weights.get(dim, 0))
        confidence = max(0.0, min(0.8, float(item.confidence)))
        effective_weight = weight * confidence
        numerator += float(item.score) * effective_weight
        denominator += effective_weight
        used[dim] = {
            "score": item.score,
            "confidence": confidence,
            "weight": weight,
        }

    if denominator == 0:
        return None, used

    return round(numerator / denominator, 2), used


def aggregate_segments(rows):
    scores = [r["score"] for r in rows if r.get("score") is not None]
    if not scores:
        return {
            "score": None,
            "segments_scored": 0,
            "mean": None,
            "peak": None,
            "coverage": 0.0,
        }

    return {
        "score": round(sum(scores) / len(scores), 2),
        "segments_scored": len(scores),
        "mean": round(sum(scores) / len(scores), 2),
        "peak": round(max(scores), 2),
        "coverage": round(len(scores) / max(1, len(rows)), 3),
    }
