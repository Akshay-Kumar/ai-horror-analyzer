from typing import Optional, List
from pydantic import BaseModel, Field


DIMENSIONS = [
    "dread",
    "suspense",
    "uncertainty",
    "vulnerability",
    "psychological",
    "atmosphere",
    "threat",
    "shock",
    "disturbance",
    "pacing",
]


class DimensionScore(BaseModel):
    score: Optional[float] = Field(default=None, ge=1, le=10)
    confidence: float = Field(default=0.0, ge=0, le=0.8)
    evidence: str = ""


class SegmentAnalysis(BaseModel):
    summary: str = ""
    visual_observations: List[str] = Field(default_factory=list)
    horror_mechanisms: List[str] = Field(default_factory=list)

    dread: DimensionScore = Field(default_factory=DimensionScore)
    suspense: DimensionScore = Field(default_factory=DimensionScore)
    uncertainty: DimensionScore = Field(default_factory=DimensionScore)
    vulnerability: DimensionScore = Field(default_factory=DimensionScore)
    psychological: DimensionScore = Field(default_factory=DimensionScore)
    atmosphere: DimensionScore = Field(default_factory=DimensionScore)
    threat: DimensionScore = Field(default_factory=DimensionScore)
    shock: DimensionScore = Field(default_factory=DimensionScore)
    disturbance: DimensionScore = Field(default_factory=DimensionScore)
    pacing: DimensionScore = Field(default_factory=DimensionScore)


class Segment(BaseModel):
    index: int
    start: float
    end: float
    frame_paths: List[str]


class MovieAnalysis(BaseModel):
    analyzer_version: str
    model_vision: str
    model_text: str
    movie: dict
    coverage: dict
    segments: List[dict]
    aggregate: dict
