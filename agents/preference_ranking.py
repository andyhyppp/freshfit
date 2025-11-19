"""Preference & Ranking agent."""

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


class CandidateScore(BaseModel):
    """Scoring metadata for a single outfit."""

    outfit_id: str
    summary: str
    context_fit: Optional[float] = None
    preference_score: Optional[float] = None
    recency_penalty: Optional[float] = None
    is_loved_combo: bool = False
    is_exploration: bool = False


class PreferenceRankingInput(BaseModel):
    """Payload provided by Outfit Designer/Parallel stack."""

    candidates: list[CandidateScore]
    context_signature: Optional[str] = None
    exploration_required: bool = True
    loved_combo_required: bool = True


class PreferenceRankingOutput(BaseModel):
    """Ordered slate returned to downstream agents."""

    ranked_outfits: list[str] = Field(default_factory=list)
    decision_trace: Optional[str] = None


INSTRUCTION = """You are the FreshFit Preference & Ranking agent.
- Analyze the candidate outfits and their scoring signals.
- Enforce guardrails: include one previously loved combo when available and one exploration outfit if provided.
- Return outfits sorted by holistic score, and include a brief decision trace describing weighting.
Output JSON that matches PreferenceRankingOutput exactly."""


def preference_ranking_agent() -> Agent:
    """Construct the Preference & Ranking agent."""

    return Agent(
        name="preference_ranking",
        description="Ranks outfit candidates with guardrails for exploration and beloved looks.",
        instruction=INSTRUCTION,
        model=Gemini(model="gemini-2.0-flash", retry_options=retry_config),
        input_schema=PreferenceRankingInput,
        output_schema=PreferenceRankingOutput,
    )

