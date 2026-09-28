from typing import List
from pydantic import BaseModel, Field

DIMENSIONS = ["dread", "suspense", "uncertainty", "vulnerability", "psychological", "atmosphere", "threat", "shock", "disturbance", "pacing"]

class MediaInfo(BaseModel):
    path: str
    filename: str
    duration_seconds: float
    width: int | None = None
    height: int | None = None
    video_codec: str | None = None
    audio_streams: int = 0
    subtitle_streams: int = 0

class Segment(BaseModel):
    index: int
    start_seconds: float
    end_seconds: float
    frame_paths: List[str] = Field(default_factory=list)
    dialogue: str = ""

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
    segment_index: int
    scores: HorrorScores
    fear_mechanisms: List[str] = Field(default_factory=list)
    explanation: str = ""
    confidence: float = Field(default=0.0, ge=0, le=1)

class MovieAnalysis(BaseModel):
    analyzer_version: str
    media: MediaInfo
    overall_horror_score: float
    scores: HorrorScores
    fear_mechanisms: List[str]
    segments: List[SegmentAnalysis]
