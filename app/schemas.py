from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict


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
    frame_paths: List[str] = Field(default_factory=list, min_length=1)


class HorrorScores(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # null means the supplied evidence is insufficient to score the dimension.
    dread: float | None = Field(default=None, ge=0, le=10)
    suspense: float | None = Field(default=None, ge=0, le=10)
    uncertainty: float | None = Field(default=None, ge=0, le=10)
    vulnerability: float | None = Field(default=None, ge=0, le=10)
    psychological: float | None = Field(default=None, ge=0, le=10)
    atmosphere: float | None = Field(default=None, ge=0, le=10)
    threat: float | None = Field(default=None, ge=0, le=10)
    shock: float | None = Field(default=None, ge=0, le=10)
    disturbance: float | None = Field(default=None, ge=0, le=10)
    pacing: float | None = Field(default=None, ge=0, le=10)


class SegmentAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)
    visual_observations: List[str] = Field(min_length=1)
    horror_mechanisms: List[str] = Field(default_factory=list)
    escalation: Literal["none", "low", "medium", "high", "unknown"]
    temporal_evidence: str = Field(min_length=1)
    scores: HorrorScores
    confidence: float = Field(ge=0, le=1)


class AnalyzedSegment(BaseModel):
    segment: Segment
    analysis: SegmentAnalysis


class MovieAnalysis(BaseModel):
    analyzer_version: str
    model: str
    media: MediaInfo
    sampled_segment_count: int
    sampled_coverage_percent: float
    segments: List[AnalyzedSegment]
    overall_horror_score: float
    dimension_scores: HorrorScores
