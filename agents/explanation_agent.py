"""Explanation agent."""

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


class ExplanationItem(BaseModel):
    """Single outfit explanation payload."""

    outfit_id: str
    summary: str
    weather_context: Optional[str] = None
    wardrobe_highlights: Optional[str] = None
    scoring_notes: Optional[str] = None


class ExplanationAgentInput(BaseModel):
    """Structured input for explanation generation."""

    items: list[ExplanationItem]
    occasion_tag: Optional[str] = None
    temp_bucket: Optional[str] = None


class ExplanationAgentOutput(BaseModel):
    """Response containing natural language rationales."""

    explanations: list[str] = Field(default_factory=list)
    selection_prompt: str = Field(
        default=(
            "Which outfit_id would you like to lock in? "
            "Reply with the id and be ready to rate all of the looks "
            "so we know what to repeat or avoid."
        ),
        description=(
            "Call-to-action that reminds the user to select an outfit and that "
            "a quick rating flow will follow for every option."
        ),
    )


INSTRUCTION = """You are the FreshFit Explanation agent.

Input:
- list of outfits: {outfits} (structured list of outfits sourced from OutfitDesigner. Each outfit mirrors the SQLite schema (outfit_id, outfit_name, outfit_description, outfit_items)).

- For each outfit, which contains top, bottom, outerwear, shoes, and accessory items etcs., craft a 1-2 sentence rationale referencing weather, occasion, color/fabric mix, and scoring highlights.
- Keep tone encouraging, note any fallback assumptions, and avoid revealing raw model/tool traces.
- Close with a concise `selection_prompt` that tells the user exactly how to choose an outfit (use `outfit_id`) and that they will rate every look afterward so Feedback & Learning can log preferences.
Return JSON strictly matching ExplanationAgentOutput."""


def explanation_agent() -> Agent:
    """Construct the Explanation agent."""

    return Agent(
        name="explanation_agent",
        description="Generates concise rationales for each outfit option.",
        instruction=INSTRUCTION,
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        input_schema=ExplanationAgentInput,
        output_schema=ExplanationAgentOutput,
        output_key="explanations",
    )
