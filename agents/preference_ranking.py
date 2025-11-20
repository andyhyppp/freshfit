"""Preference & Ranking agent."""

from typing import Optional

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types
from pydantic import BaseModel, Field

from tools.preference_history_tool import preference_history_tool

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

    user_id: str = Field(
        default="123",
        description="Identifier for the wearer; use when calling tooling for history.",
    )
    candidates: list[CandidateScore]
    context_signature: Optional[str] = None
    exploration_required: bool = True
    loved_combo_required: bool = True


class PreferenceRankingOutput(BaseModel):
    """Ordered slate returned to downstream agents."""

    ranked_outfits: list[str] = Field(default_factory=list)
    decision_trace: Optional[str] = None


INSTRUCTION = """You are the FreshFit Preference & Ranking agent.
outfit_designer input is: {outfits}

- Analyze the candidate outfits and their scoring signals.
- When preference history is missing or stale, call `preference_history_tool` with the user_id to pull outfits/items the user rated 4-5 (liked) and 1 (disliked). Use this data to honor loved combos and avoid banned pieces.
- Enforce guardrails: include one previously loved combo when available and one exploration outfit provided from outfit_designer.
- Return outfits sorted by holistic score, and include a brief decision trace describing weighting.
Output JSON that matches PreferenceRankingOutput exactly."""


def preference_ranking_agent() -> Agent:
    """Construct the Preference & Ranking agent."""

    return Agent(
        name="preference_ranking",
        description="Ranks outfit candidates with guardrails for exploration and beloved looks.",
        instruction=INSTRUCTION,
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        input_schema=PreferenceRankingInput,
        output_schema=PreferenceRankingOutput,
        tools=[preference_history_tool],
    )
