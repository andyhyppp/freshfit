"""Metrics agent."""

from typing import Optional

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types
from pydantic import BaseModel, Field

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)


class MetricsRequest(BaseModel):
    """Request payload for metrics rollups."""

    start_date: str
    end_date: Optional[str] = None
    include_travel: bool = True


class MetricsResponse(BaseModel):
    """Aggregated KPI snapshot."""

    acceptance_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    average_rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    banned_combo_count: Optional[int] = Field(default=None, ge=0)
    travel_coverage_ratio: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    notes: Optional[str] = None


INSTRUCTION = """You are the FreshFit Metrics agent.
- Summarize FreshFit KPIs (acceptance, average rating, banned combo count, travel coverage) for the requested date range.
- Call the Metrics Tool when available; otherwise describe fallback assumptions.
Return JSON matching MetricsResponse."""


def metrics_agent() -> Agent:
    """Construct the Metrics agent."""

    return Agent(
        name="metrics_agent",
        description="Produces KPI snapshots for FreshFit.",
        instruction=INSTRUCTION,
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        input_schema=MetricsRequest,
        output_schema=MetricsResponse,
    )
