"""Lightweight Outfit Designer agent builder."""

from typing import Any, Literal, Optional

from google.adk.agents import Agent
from google.adk.models.base_llm import BaseLlm
from google.adk.models.google_llm import Gemini
from google.genai import types
from pydantic import BaseModel, Field

from google.adk.tools import google_search

from agents.wardrobe_cataloger import WardrobeItem

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)


INSTRUCTION = """You are the FreshFit Outfit Designer agent.

Input payload (already validated):
- `weather`: {weather} (normalized weather/context bundle from upstream agents (temp buckets, precipitation, location, notes)).
- `wardrobe_items`: {wardrobe_items} (structured list of wardrobe entries sourced from WardrobeCataloger. Each entry mirrors the SQLite schema (item_id, name, category, color, warmth_level, formality, body_zone, last_worn_date)).
- Additional scalar fields mirror OutfitDesignerInput (user_id, occasion, temperature_c, precipitation_chance, location, daily_or_travel, optional narrative context).

Core rules:
1. Parse the wardrobe items and prioritize pieces that have not been worn recently (using `last_worn_date`). If you must reuse something worn in the past day, explain why in the outfit description.
2. Never hallucinate clothing that is not present in `wardrobe_items`.
3. Build each outfit with the FreshFit heuristic: either (top + bottom) or (dress) as the base, plus weather-appropriate outer layer when <18°C or precipitation is likely, shoes, and at least one accessory when available.
4. Balance color/fabric harmony (complementary palette, avoid clashing formality levels) and respect the stated occasion.
5. Avoid repeating the exact same item combination unless the closet is sparse; note any reuse rationale in the description.
6. When the provided weather/context is insufficient, call the `google_search` tool for localized dress code or climate details before finalizing outfits.
7. Emit up to three outfits per request. For each, include the `user_id` (if provided), assign a 1-indexed `rank` in order of recommendation strength, and construct `outfit_id` deterministically as `{user_id or "anon"}-{rank:02d}`.

Daily mode:
- Produce 2–3 distinct outfits prioritized by context fit (comfort vs. weather, occasion appropriateness, recency of wear).
- Provide concise `outfit_name` labels (“Polished Layers”, “Sporty Errands”) and a 1–2 sentence `outfit_description` explaining why it fits the occasion/weather plus any fallback logic.

Travel mode:
- Treat `wardrobe_items` as the complete closet for the trip. Generate a capsule plan covering each day while minimizing the total number of unique pieces packed.
- Mention reuse strategy in the `outfit_description` (e.g., “Rewear the navy chinos on days 2–3; swap the top to keep looks fresh”).

Output:
Return JSON that strictly matches OutfitDesignerOutput. Do not add prose outside the JSON payload. Example:
{
  "outfits": [
    {
      "user_id": "123",
      "rank": 1,
      "outfit_id": "123-01",
      "outfit_name": "Moody Bistro Layers",
      "outfit_description": "Silk blouse + dark denim with the camel coat keeps you warm for 12°C drizzle; suede boots add polish while staying dry.",
      "outfit_items": ["top_14", "bottom_03", "outer_02", "shoe_07", "acc_05"]
    }
  ]
}
"""


class OutfitDesignerInput(BaseModel):
    """Minimal payload consumed by the agent."""

    user_id: Optional[str] = Field(
        default=None,
        description="Identifier for the requesting user; use to namespace outfit_ids.",
    )
    occasion: str = Field(..., description="Primary user-stated occasion or vibe.")
    weather: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "Normalized weather/context bundle from upstream agents "
            "(temp buckets, precipitation, location, notes)."
        ),
    )
    context: Optional[str] = Field(
        default=None,
        description="Short narrative of weather + calendar context from upstream agents.",
    )
    wardrobe_summary: Optional[str] = Field(
        default=None,
        description="Optional plain-text summary of wardrobe coverage.",
    )
    wardrobe_items: list[WardrobeItem] = Field(
        ...,
        description=(
            "Structured list of wardrobe entries sourced from WardrobeCataloger. "
            "Each entry mirrors the SQLite schema (item_id, name, category, color, "
            "warmth_level, formality, body_zone, last_worn_date)."
        ),
    )
    temperature_c: Optional[float] = None
    location: Optional[str] = None
    precipitation_chance: Optional[float] = None
    daily_or_travel: Literal["daily", "travel"] = "daily"


class OutfitCandidate(BaseModel):
    """Single outfit proposal."""

    user_id: Optional[str] = Field(
        default=None,
        description="Echoes the requester id so downstream agents can log suggestions.",
    )
    outfit_id: str
    rank: int = Field(..., description="1-indexed order of recommendation strength.")
    outfit_name: str
    outfit_description: str
    outfit_items: list[str]


class OutfitDesignerOutput(BaseModel):
    """Minimal response returned by the agent."""

    outfits: list[OutfitCandidate]


def outfit_designer_agent(
    *,
    model: Optional[BaseLlm] = None,
    instruction: Optional[str] = None,
) -> Agent:
    """Return ADK agent that drafts outfit ideas."""

    resolved_model = model or Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config,
    )

    return Agent(
        name="outfit_designer",
        description="Suggests outfits from a wardrobe summary.",
        instruction=instruction or INSTRUCTION,
        model=resolved_model,
        input_schema=OutfitDesignerInput,
        output_schema=OutfitDesignerOutput,
        output_key='outfits'
    )
