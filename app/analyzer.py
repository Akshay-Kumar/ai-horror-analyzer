from pathlib import Path
import base64
import json
import requests
from schemas import SegmentAnalysis


VISION_SYSTEM = r"""
You are the visual evidence stage of a horror-analysis pipeline.

Analyze only what is visually supported by the supplied movie frames. Do not use
public reviews, ratings, genre databases, or outside knowledge.

Your job is NOT to assign horror scores. Produce detailed factual observations that
a second model can use to score horror effectiveness.

For each frame, identify concrete visible evidence such as:
- people, creatures, objects, injuries, facial expressions
- lighting, color, shadows, darkness, isolation
- composition, distance, camera-visible threat cues
- unusual or disturbing imagery
- environmental details that visibly support fear or unease

Then identify plausible horror mechanisms ONLY when supported by the frames.

Important:
- Never invent off-screen events.
- Never infer that an ordinary person/object is dangerous without visual evidence.
- Do not claim that something is moving from a still frame.
- Do not infer pacing, jump scares, suspense timing, or escalation from still images alone.
- If something is ambiguous, explicitly call it ambiguous.
- Be concise but information-dense.
""".strip()


TEXT_SYSTEM = r"""
You are the scoring stage of a horror-analysis pipeline.

You receive factual visual observations from movie frames plus segment timing.
Convert that evidence into a strict JSON horror analysis.

Do not use public reviews, ratings, popularity, genre labels, or outside knowledge.
Do not invent events that are not supported by the evidence.

Scoring rules:
- Scores are 1-10 only when the supplied evidence supports the dimension.
- Use null when the evidence is insufficient.
- Confidence must be 0.0-0.8.
- Never infer temporal properties from a few still frames.
- suspense, shock, and pacing normally require temporal/audio evidence. With only
  still frames, use null unless the evidence itself directly supports a limited
  observation.
- vulnerability and threat require an observable source of danger or exposure.
- dread can be scored only when the visual evidence itself supports ominous,
  threatening, or foreboding conditions.
- atmosphere can be scored from lighting, setting, composition, isolation, etc.
- disturbance can be scored from clearly disturbing imagery.
- psychological can be scored only when visual evidence supports psychological
  unease, identity disruption, expressions, apparent distress, uncanny imagery,
  etc.
- uncertainty can be scored when the frames visibly contain ambiguity, obscurity,
  concealment, or unclear identity/source.
- Do not give high scores merely because a movie is known to be horror.

Return JSON matching the supplied schema exactly.
""".strip()


class OllamaV5:
    def __init__(
        self,
        vision_model="qwen3-vl:8b",
        text_model="qwen3:4b",
        host="http://127.0.0.1:11434",
        timeout=600,
    ):
        self.vision_model = vision_model
        self.text_model = text_model
        self.host = host.rstrip("/")
        self.timeout = timeout

    def _chat(self, payload: dict) -> dict:
        response = requests.post(
            f"{self.host}/api/chat",
            json=payload,
            timeout=self.timeout,
        )
        if not response.ok:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise RuntimeError(
                f"Ollama API error {response.status_code}: {detail}"
            )
        return response.json()

    @staticmethod
    def _image_b64(path: str) -> str:
        return base64.b64encode(Path(path).read_bytes()).decode("ascii")

    def vision_stage(self, frame_paths: list[str], start: float, end: float) -> str:
        prompt = (
            f"Analyze this {end-start:.0f}-second movie segment. "
            f"Approximate segment time: {start:.1f}-{end:.1f} seconds. "
            "Describe the visible evidence for a downstream horror scorer."
        )

        # Ollama's /api/chat endpoint uses a string `content` plus an
        # `images` array of base64-encoded images. It does NOT use the
        # OpenAI-style `content: [{type: image_url, ...}]` format here.
        images = [self._image_b64(path) for path in frame_paths]

        payload = {
            "model": self.vision_model,
            "messages": [
                {"role": "system", "content": VISION_SYSTEM},
                {"role": "user", "content": prompt, "images": images},
            ],
            "stream": False,
            "think": True,
            "options": {
                "temperature": 0,
                "num_ctx": 8192,
                "num_predict": 4096,
            },
            "keep_alive": "15m",
        }

        data = self._chat(payload)
        message = data.get("message", {})
        content_text = (message.get("content") or "").strip()
        thinking = (message.get("thinking") or "").strip()

        # Qwen3-VL can place the useful reasoning in thinking even when content
        # is empty. That is intentional in V5: the second model consumes it.
        evidence = content_text or thinking
        if not evidence:
            raise RuntimeError(
                "Vision model returned neither content nor thinking. "
                f"Model={self.vision_model}; response keys={list(data.keys())}"
            )

        return evidence

    def score_stage(
        self,
        evidence: str,
        start: float,
        end: float,
    ) -> SegmentAnalysis:
        schema = SegmentAnalysis.model_json_schema()

        user_prompt = f"""
Segment: {start:.1f} - {end:.1f} seconds

VISUAL EVIDENCE FROM THE VISION MODEL:
--- BEGIN EVIDENCE ---
{evidence}
--- END EVIDENCE ---

Now produce the final structured horror analysis for this segment.

The JSON must contain:
- summary
- visual_observations
- horror_mechanisms
- dread
- suspense
- uncertainty
- vulnerability
- psychological
- atmosphere
- threat
- shock
- disturbance
- pacing

Each dimension must contain:
{{
  "score": number from 1 to 10 OR null,
  "confidence": number from 0.0 to 0.8,
  "evidence": "brief evidence-based explanation"
}}

JSON schema:
{json.dumps(schema, indent=2)}
""".strip()

        payload = {
            "model": self.text_model,
            "messages": [
                {"role": "system", "content": TEXT_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "think": False,
            "format": schema,
            "options": {
                "temperature": 0,
                "num_ctx": 8192,
                "num_predict": 4096,
                # Keep the small text model off the GPU so it does not fight
                # the 8B vision model for the user's 12 GB VRAM.
                "num_gpu": 0,
            },
            "keep_alive": "5m",
        }

        data = self._chat(payload)
        message = data.get("message", {})
        content_text = (message.get("content") or "").strip()

        if not content_text:
            thinking = (message.get("thinking") or "").strip()
            raise RuntimeError(
                "Text scoring model returned no final JSON. "
                f"content_length={len(content_text)}, "
                f"thinking_length={len(thinking)}"
            )

        try:
            return SegmentAnalysis.model_validate_json(content_text)
        except Exception as exc:
            raise RuntimeError(
                "Text scoring model returned invalid JSON.\n"
                f"Raw response:\n{content_text}"
            ) from exc
