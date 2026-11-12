"""Pydantic checks untrusted requests and model-selected arguments."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Question(StrictModel):
    question: str = Field(min_length=3, max_length=1000)

    @field_validator("question")
    @classmethod
    def not_blank(cls, value):
        if len(value.strip()) < 3:
            raise ValueError("Question must contain at least three non-space characters")
        return value.strip()


class AnalysisArgs(StrictModel):
    metric: Literal[
        "national_demand_mw",
        "transmission_demand_mw",
        "embedded_wind_generation",
        "embedded_solar_generation",
    ]
    analysis: Literal["monthly", "peak", "period_profile", "summary"]
    month: int | None = Field(ge=1, le=12)


class SearchArgs(StrictModel):
    query: str = Field(min_length=3, max_length=1000)


class RefusalArgs(StrictModel):
    reason: Literal["outside_scope", "unsupported_analysis", "needs_clarification"]


class Source(StrictModel):
    id: str
    title: str
    url: str
    text: str
    score: float


class Evidence(StrictModel):
    id: str
    kind: Literal["sql", "documentation", "refusal"]
    tool: str
    arguments: dict[str, Any]
    result: dict[str, Any]


class Answer(StrictModel):
    answer: str
    evidence: list[Evidence]
    sources: list[Source]
    mode: Literal["live_llm", "direct_tool"]
    model: str | None
    limitations: list[str]
