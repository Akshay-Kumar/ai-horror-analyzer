from pathlib import Path

from .schemas import HorrorScores, Segment, SegmentAnalysis


class HorrorAnalyzer:
    """
    Provider-independent interface.

    Replace analyze_segment() with the real multimodal model implementation.
    Keeping this interface separate means the rest of the application does not
    care whether the backend is OpenAI, a local model, or a hybrid pipeline.
    """

    VERSION = "placeholder-v1"

    def analyze_segment(self, segment: Segment) -> SegmentAnalysis:
        # Deliberately conservative placeholder values.
        # These are NOT presented as real AI ratings.
        scores = HorrorScores(
            dread=0.0,
            suspense=0.0,
            uncertainty=0.0,
            vulnerability=0.0,
            psychological=0.0,
            atmosphere=0.0,
            threat=0.0,
            shock=0.0,
            disturbance=0.0,
            pacing=0.0,
        )

        return SegmentAnalysis(
            segment_index=segment.index,
            scores=scores,
            fear_mechanisms=[],
            explanation="Placeholder analyzer. Real multimodal analysis is not enabled yet.",
            confidence=0.0,
        )
