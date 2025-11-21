"""Lightweight Outfit Designer agent builder."""

from typing import Any, Literal, Optional

from google.adk.agents import Agent
from google.adk.models.base_llm import BaseLlm
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search
from google.genai import types
from pydantic import BaseModel, Field, model_validator

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
7. When `daily_or_travel` is "daily", emit **at least five and no more than ten** outfits per request. When in travel mode, emit enough outfits to cover the trip itinerary. For every outfit, include the `user_id` (if provided), assign a 1-indexed `rank` in order of recommendation strength, and construct `outfit_id` deterministically as `{user_id or "anon"}-{rank:02d}`.
8. For every outfit, emit BOTH `outfit_items` (list of item_ids only) and `outfit_item_details` (list of objects that pair each item_id with a 2-4 word `short_name` pulled verbatim from the wardrobe item name). Keep the ordering consistent between the two lists.

Daily mode:
- Produce at least 5 and no more than 10 distinct outfits prioritized by context fit (comfort vs. weather, occasion appropriateness) before handing off to downstream agents.
- Provide concise `outfit_name` labels (“Polished Layers”, “Sporty Errands”).

Travel mode:
- Treat `wardrobe_items` as the complete closet for the trip. Generate a capsule plan covering each day while minimizing the total number of unique pieces packed.
- Mention reuse strategy in the `outfit_description` (e.g., “Rewear the navy chinos on days 2–3; swap the top to keep looks fresh”).

Output:
Return JSON that strictly matches OutfitDesignerOutput. Do not add prose outside the JSON payload. Example:
{
  "outfits": [
    {
      "user_id": "123",
      "outfit_id": "123-01",
      "outfit_name": "Moody Bistro Layers",
      "outfit_description": "Silk blouse + dark denim with the camel coat keeps you warm for 12°C drizzle; suede boots add polish while staying dry.",
      "outfit_items": ["top_14", "bottom_03", "outer_02", "shoe_07", "acc_05"],
      "outfit_item_details": [
        {"item_id": "top_14", "short_name": "Ivory Silk Blouse"},
        {"item_id": "bottom_03", "short_name": "Dark Wash Denim"},
        {"item_id": "outer_02", "short_name": "Camel Wool Coat"},
        {"item_id": "shoe_07", "short_name": "Suede Boots"},
        {"item_id": "acc_05", "short_name": "Graphite Wool Scarf"}
      ]
    },
    {
      "user_id": "123",
      "outfit_id": "123-02",
      "outfit_name": "Gallery Hop Minimalist",
      "outfit_description": "Black mock-neck with charcoal trousers, the cropped denim jacket, and white court sneakers keeps things polished but relaxed for mild afternoons.",
      "outfit_items": ["top_09", "bottom_11", "outer_05", "shoe_03", "acc_02"],
      "outfit_item_details": [
        {"item_id": "top_09", "short_name": "Black Mock-Neck Top"},
        {"item_id": "bottom_11", "short_name": "Charcoal Tailored Trousers"},
        {"item_id": "outer_05", "short_name": "Washed Denim Jacket"},
        {"item_id": "shoe_03", "short_name": "White Court Sneakers"},
        {"item_id": "acc_02", "short_name": "Gold Statement Necklace"}
      ]
    },
    ...more outfits...
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


class OutfitItemDetail(BaseModel):
    """Readable mapping for each wardrobe item included in an outfit."""

    item_id: str = Field(
        ...,
        description="Unique wardrobe identifier referenced in outfit_items.",
    )
    short_name: str = Field(
        ...,
        description="2-4 word name copied from the wardrobe entry so users can scan quickly.",
    )


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
    outfit_item_details: list[OutfitItemDetail] = Field(
        ...,
        description=(
            "List pairing each outfit item_id with a short_name pulled from the wardrobe."
        ),
    )


class OutfitDesignerOutput(BaseModel):
    """Minimal response returned by the agent."""

    outfits: list[OutfitCandidate]

    @model_validator(mode="after")
    def ensure_multiple_outfits(
        cls, model: "OutfitDesignerOutput"
    ) -> "OutfitDesignerOutput":
        """Guard against single-look payloads."""

        outfits = model.outfits or []
        if len(outfits) < 3:
            raise ValueError(
                "Generate at least two distinct outfits before returning the slate."
            )
        return model


def outfit_designer_agent(
    *,
    model: Optional[BaseLlm] = None,
    instruction: Optional[str] = None,
) -> Agent:
    """Return ADK agent that drafts outfit ideas."""

    resolved_model = model or Gemini(
        model="gemini-2.5-flash",
        retry_options=retry_config,
    )

    return Agent(
        name="outfit_designer",
        description="Suggests outfits from a wardrobe summary.",
        instruction=INSTRUCTION,
        model=resolved_model,
        input_schema=OutfitDesignerInput,
        output_schema=OutfitDesignerOutput,
        output_key="outfits",
        tools=[google_search],
    )
