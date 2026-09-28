from pathlib import Path
import json
import re

from ollama import Client

from .schemas import Segment, SegmentAnalysis


SYSTEM_PROMPT = """
You are a forensic horror-content analyst.

Analyze ONLY the supplied movie frames and their chronological order.

Do not use:
- public reviews
- genre reputation
- outside plot knowledge
- filename information
- assumptions about the movie

Do not decide whether the movie is good or bad.

Your task is to identify observable visual mechanisms that can contribute
to horror effectiveness.

EVIDENCE RULES:

1. Separate OBSERVATION from INFERENCE.
2. Every visual observation must describe something actually visible.
3. Never invent a character's motive, supernatural cause, off-screen event,
   identity, or threat.
4. If a dimension cannot be supported by the supplied frames, return null.
5. Three still frames cannot reliably establish audio, dialogue, a jump scare,
   or exact editing rhythm.
6. A cut between two different shots is NOT itself evidence of a jump scare.
7. Pacing should normally be null unless the frames provide meaningful
   evidence of temporal progression or repeated escalation.
8. Shock should normally be null or low unless there is clear evidence of
   a sudden visual reveal or abrupt visual change.
9. Do not infer horror merely because an image is dark.
10. Do not call an ordinary person or object a threat unless the supplied
    images provide visible evidence supporting that interpretation.
11. Confidence must reflect the evidence available in these frames.
    With only three still frames and no audio/subtitles, confidence must
    not exceed 0.80.

DIMENSIONS:

- dread: anticipation or ominous implication of something feared.
- suspense: unresolved danger or anticipation of an outcome.
- uncertainty: missing information, concealment, ambiguity, unpredictability.
- vulnerability: exposed, isolated, helpless, defenseless, or trapped subjects.
- psychological: uncanny perception, identity, obsession, guilt, sanity,
  paranoia, or related mechanisms visibly supported by the frames.
- atmosphere: lighting, setting, composition, isolation, claustrophobia,
  environmental unease.
- threat: visible or strongly implied danger supported by the images.
- shock: sudden visual revelation or abrupt visual change supported by the
  chronological frame sequence.
- disturbance: grotesque, uncanny, visceral, taboo, or deeply unsettling
  imagery.
- pacing: apparent escalation or rhythm supported by the chronological samples.

REQUIRED OUTPUT:

Provide:

1. A concise summary.
2. At least two concrete visual observations.
3. Horror mechanisms only when supported by evidence.
4. Temporal evidence describing actual changes between frames.
5. Scores only for dimensions supported by the evidence.
6. Null for dimensions that cannot reasonably be determined.
7. A calibrated confidence.

Return ONLY valid JSON matching the supplied schema.
Do not use Markdown.
Do not use ```json fences.
"""


USER_TEMPLATE = """
Analyze this {duration:.0f}-second movie segment.

The frames are chronological:

{frame_list}

Important:

Do not infer anything from the filename.
Do not use knowledge of the movie.
Do not treat a scene cut as a horror event by itself.

Describe what is visibly present and what actually changes between
the sampled frames.

Then score only the horror dimensions supported by those observations.
"""


class HorrorAnalyzer:
    def __init__(
        self,
        model: str = "qwen3-vl:8b",
        host: str = "http://127.0.0.1:11434",
        num_ctx: int = 8192,
    ):
        self.model = model
        self.client = Client(host=host)
        self.num_ctx = num_ctx

    def _extract_json(self, content: str) -> str:
        """
        Extract JSON if the model accidentally wraps it in Markdown.
        """
        content = content.strip()

        if not content:
            raise ValueError("Ollama returned an empty response.")

        # Normal JSON response
        if content.startswith("{") and content.endswith("}"):
            return content

        # Handle ```json ... ``` just in case
        match = re.search(
            r"```(?:json)?\s*(\{.*\})\s*```",
            content,
            flags=re.DOTALL,
        )

        if match:
            return match.group(1)

        # Last attempt: locate the outer JSON object
        start = content.find("{")
        end = content.rfind("}")

        if start >= 0 and end > start:
            return content[start:end + 1]

        raise ValueError(
            f"Ollama returned non-JSON content:\n{content[:2000]}"
        )

    def analyze_segment(self, segment: Segment) -> SegmentAnalysis:

        frame_names = "\n".join(
            f"Frame {i + 1}: {Path(p).name}"
            for i, p in enumerate(segment.frame_paths)
        )

        prompt = USER_TEMPLATE.format(
            duration=segment.end_seconds - segment.start_seconds,
            frame_list=frame_names,
        )

        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                    "images": segment.frame_paths,
                },
            ],
            format=SegmentAnalysis.model_json_schema(),
            options={
                "temperature": 0,
                "num_ctx": self.num_ctx,
            },
            think=False,
            stream=False,
        )

        content = response.message.content or ""

        if not content.strip():
            print("\nERROR: Ollama returned an empty response.")
            print(f"Model: {self.model}")

            if hasattr(response, "message"):
                print(f"Message: {response.message}")

            raise RuntimeError(
                "Ollama returned empty content. "
                "See diagnostic information above."
            )

        try:
            json_content = self._extract_json(content)
            return SegmentAnalysis.model_validate_json(json_content)

        except Exception as exc:
            print("\nERROR: Could not parse Ollama response.")
            print("\nRaw Ollama response:")
            print("--------------------------------------------------")
            print(content)
            print("--------------------------------------------------")

            raise RuntimeError(
                f"Failed to parse structured Ollama response: {exc}"
            ) from exc