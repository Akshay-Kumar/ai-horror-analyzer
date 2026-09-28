from pathlib import Path
from ollama import Client
from .schemas import Segment, SegmentAnalysis

SYSTEM_PROMPT = """
You are a forensic horror-content analyst. Analyze only the supplied movie frames and their temporal order.
Do not use public reviews, genre reputation, outside plot knowledge, or assumptions about the movie.
Do not decide whether the movie is good or bad. Measure observable mechanisms that can contribute to horror effectiveness.

Important scoring rules:
- Scores are 0-10 and should reflect evidence in the supplied frames.
- Do not invent events that are not visible.
- A still image cannot establish a jump scare. Keep shock low unless the frame sequence provides evidence of a sudden reveal.
- Pacing is about apparent temporal change across the supplied frames; if insufficient evidence exists, use a conservative score and explain it.
- Dread concerns anticipation or ominous implication, not merely ugliness.
- Suspense concerns unresolved threat or anticipation.
- Uncertainty concerns missing information, concealment, ambiguity, or unpredictability.
- Vulnerability concerns exposed, isolated, helpless, or defenseless subjects.
- Psychological concerns fear mechanisms involving perception, identity, sanity, obsession, guilt, uncanny implications, etc.
- Atmosphere concerns lighting, setting, composition, soundless visual mood, isolation, claustrophobia, and environmental unease.
- Threat concerns visible or strongly implied danger.
- Shock concerns sudden visual revelation or abrupt change evidenced by the frame sequence.
- Disturbance concerns visceral, uncanny, grotesque, taboo, or deeply unsettling imagery.

Return concise but evidence-based observations. Separate what is visible from what is inferred.
"""

USER_TEMPLATE = """
Analyze this {duration:.0f}-second movie segment.

The frames are supplied in chronological order:
{frame_list}

Explain what changes between the frames, if anything. Then score the ten horror dimensions.
Use the requested structured format. Do not output markdown or extra fields.
"""


class HorrorAnalyzer:
    def __init__(self, model: str = "qwen3-vl:8b", host: str = "http://127.0.0.1:11434"):
        self.model = model
        self.client = Client(host=host)

    def analyze_segment(self, segment: Segment) -> SegmentAnalysis:
        frame_names = "\n".join(
            f"Frame {i + 1}: {Path(p).name}" for i, p in enumerate(segment.frame_paths)
        )
        prompt = USER_TEMPLATE.format(
            duration=segment.end_seconds - segment.start_seconds,
            frame_list=frame_names,
        )
        response = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": prompt,
                    "images": segment.frame_paths,
                },
            ],
            format=SegmentAnalysis.model_json_schema(),
            options={"temperature": 0},
            stream=False,
        )
        return SegmentAnalysis.model_validate_json(response.message.content)
