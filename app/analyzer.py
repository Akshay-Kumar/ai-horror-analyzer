import base64
import mimetypes
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from .schemas import Segment, SegmentAnalysis

load_dotenv()

ANALYSIS_INSTRUCTIONS = """
You are the horror-analysis engine for a content-based movie analyzer.

Analyze ONLY the supplied representative video frames and any supplied dialogue.
Do not use public reviews, ratings, IMDb, Rotten Tomatoes, Reddit, popularity,
or outside knowledge about the movie.

Estimate how effectively THIS SEGMENT uses mechanisms commonly associated with
inducing fear or horror in a viewer. Score every dimension from 0 to 10.
Do not equate darkness, blood, violence, or a monster with high horror automatically.
A quiet scene can score highly for dread or suspense if the evidence supports it.
Base scores on observable evidence and use confidence to reflect evidence quality.
Return 3–8 short fear-mechanism labels when applicable. Do not give an overall movie
rating here.

Definitions:
DREAD = anticipation that something bad is approaching or may happen.
SUSPENSE = tension created by waiting to discover what happens next.
UNCERTAINTY = lack of knowledge about threat, situation, outcome, or reality.
VULNERABILITY = how exposed, trapped, helpless, isolated, or unable to protect characters appear.
PSYCHOLOGICAL = fear involving paranoia, loss of control, identity, trauma, obsession, etc.
ATMOSPHERE = setting, lighting, composition, environment, silence, and visual mood.
THREAT = seriousness, proximity, capability, or apparent inevitability of danger.
SHOCK = sudden scares, startling events, abrupt revelations, or sudden sensory changes.
DISTURBANCE = unsettling, grotesque, uncanny, disturbing, or uncomfortable qualities.
PACING = how effectively the scene builds, maintains, or releases horror tension.
"""

def _image_data_url(path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(path.name)
    mime_type = mime_type or "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"

class HorrorAnalyzer:
    VERSION = "openai-multimodal-v1"
    def __init__(self, model: str | None = None):
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not set. Copy .env.example to .env and add your API key.")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.5")
        self.client = OpenAI()

    def analyze_segment(self, segment: Segment) -> SegmentAnalysis:
        content = [{"type": "input_text", "text": f"Analyze movie segment {segment.index} ({segment.start_seconds:.1f}s to {segment.end_seconds:.1f}s).\n\nDialogue/subtitles:\n{segment.dialogue or '[No dialogue/subtitles supplied]'}"}]
        for frame_path in segment.frame_paths:
            content.append({"type": "input_image", "image_url": _image_data_url(Path(frame_path)), "detail": "high"})
        response = self.client.responses.parse(model=self.model, instructions=ANALYSIS_INSTRUCTIONS, input=[{"role": "user", "content": content}], text_format=SegmentAnalysis)
        for output in response.output:
            if output.type != "message":
                continue
            for item in output.content:
                if item.type == "output_text" and item.parsed is not None:
                    item.parsed.segment_index = segment.index
                    return item.parsed
        raise RuntimeError(f"Model returned no structured SegmentAnalysis for segment {segment.index}.")
