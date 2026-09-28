from pathlib import Path
from ollama import Client
from .schemas import Segment, SegmentAnalysis

SYSTEM_PROMPT = """
You are a forensic horror-content analyst.
Analyze ONLY the supplied movie frames and their chronological order.
Do not use public reviews, genre reputation, outside plot knowledge, or assumptions about the movie.
Do not decide whether the movie is good or bad.
Measure observable visual mechanisms that can contribute to horror effectiveness.

Evidence rules:
1. Separate OBSERVATION from INFERENCE. Only state an inference when the visible evidence reasonably supports it.
2. Never invent a character's motive, supernatural cause, off-screen event, identity, or threat.
3. If a dimension cannot be supported by the supplied frames, return null for that dimension rather than guessing.
4. Three still frames cannot reliably establish audio, dialogue, a jump scare, or exact editing rhythm. Do not pretend they can.
5. A cut between two different shots is not itself evidence of a jump scare or escalating horror.
6. Pacing should be null unless the supplied frames provide meaningful evidence of temporal progression or repeated escalation.
7. Shock should normally be null or low unless there is clear evidence of a sudden visual reveal/change between the supplied frames.
8. Confidence is confidence in THIS analysis from THIS evidence, not confidence that the movie is objectively scary. With only three still frames and no audio/subtitles, do not use confidence above 0.80.

Dimension definitions:
- dread: anticipation or ominous implication of something feared.
- suspense: unresolved danger or anticipation of an outcome.
- uncertainty: missing information, concealment, ambiguity, or unpredictability.
- vulnerability: exposed, isolated, helpless, defenseless, or trapped subjects.
- psychological: uncanny perception, identity, obsession, guilt, sanity, paranoia, or related mechanisms visibly supported by the frames.
- atmosphere: lighting, setting, composition, isolation, claustrophobia, and environmental unease.
- threat: visible or strongly implied danger supported by the images.
- shock: sudden visual revelation or abrupt visual change supported by the frame sequence.
- disturbance: grotesque, uncanny, visceral, taboo, or deeply unsettling imagery.
- pacing: apparent escalation or rhythm supported by the supplied chronological samples.

For every segment, provide:
- a concise summary;
- at least 2 concrete visual_observations, each tied to something visible;
- horror_mechanisms only when supported;
- temporal_evidence describing actual changes between frames;
- scores, using null where evidence is insufficient;
- a calibrated confidence.

Return only the requested structured data.
"""

USER_TEMPLATE = """
Analyze this {duration:.0f}-second movie segment.

Frames are chronological:
{frame_list}

Do not infer anything from the filename or from knowledge of the movie.
Do not treat a scene cut as a horror event by itself.
Explain what is visibly present and what actually changes between the sampled frames.
Then score only the dimensions supported by those observations.
"""


class HorrorAnalyzer:
    def __init__(self, model: str = "qwen3-vl:8b", host: str = "http://127.0.0.1:11434", num_ctx: int = 8192):
        self.model = model
        self.client = Client(host=host)
        self.num_ctx = num_ctx

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
            options={"temperature": 0, "num_ctx": self.num_ctx},
            stream=False,
        )
        return SegmentAnalysis.model_validate_json(response.message.content)
