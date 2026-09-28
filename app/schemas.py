from typing import List, Literal
from pydantic import BaseModel, Field


class MediaInfo(BaseModel):
    path: str
    filename: str
    duration_seconds: float
    width: int
    height: int
    video_codec: str | None = None
    audio_streams: int = 0
    subtitle_streams: int = 0


class Segment(BaseModel):
    index: int
    start_seconds: float
    end_seconds: float
    frame_paths: List[str] = Field(default_factory=list)


class HorrorScores(BaseModel):
    dread: float = Field(ge=0, le=10)
    suspense: float = Field(ge=0, le=10)
    uncertainty: float = Field(ge=0, le=10)
    vulnerability: float = Field(ge=0, le=10)
    psychological: float = Field(ge=0, le=10)
    atmosphere: float = Field(ge=0, le=10)
    threat: float = Field(ge=0, le=10)
    shock: float = Field(ge=0, le=10)
    disturbance: float = Field(ge=0, le=10)
    pacing: float = Field(ge=0, le=10)


class SegmentAnalysis(BaseModel):
    summary: str
    visual_observations: List[str] = Field(default_factory=list)
    horror_mechanisms: List[str] = Field(default_factory=list)
    escalation: Literal["none", "low", "medium", "high", "unknown"]
    temporal_evidence: str
    scores: HorrorScores
    confidence: float = Field(ge=0, le=1)


class AnalyzedSegment(BaseModel):
    segment: Segment
    analysis: SegmentAnalysis


class MovieAnalysis(BaseModel):
    analyzer_version: str
    model: str
    media: MediaInfo
    segments: List[AnalyzedSegment]
    overall_horror_score: float
    dimension_scores: HorrorScores
