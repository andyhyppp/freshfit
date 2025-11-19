"""Wardrobe Cataloger agent"""

from typing import Optional

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types
from pydantic import BaseModel, Field

from tools.demo_wardrobe_tool import demo_wardrobe_tool

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)


class WardrobeItem(BaseModel):
    """Individual wardrobe entry tracked by the cataloger."""

    item_id: str
    user_id: Optional[str] = None
    name: str
    category: str
    color: Optional[str] = None
    warmth_level: Optional[str] = None
    formality: Optional[str] = None
    body_zone: Optional[str] = None
    last_worn_date: Optional[str] = None


class WardrobeCatalogerInput(BaseModel):
    """Payload received from the orchestrator."""

    user_id: str = Field(
        default="123",
        description="Demo user identifier used when querying the wardrobe DB.",
    )
    items: list[WardrobeItem] = Field(
        default_factory=list,
        description=(
            "Optional pre-fetched wardrobe items. When empty, call the demo wardrobe tool."
        ),
    )
    required_categories: list[str] = Field(
        default_factory=list,
        description="Categories that must be represented in the clean set (e.g., top, bottom).",
    )
    banned_items: list[str] = Field(default_factory=list)


class WardrobeCatalogerOutput(BaseModel):
    """Structured response consumed by downstream agents."""

    wardrobe_items: list[WardrobeItem] = Field(
        default_factory=list,
        description=(
            "Hydrated wardrobe entries sourced from the SQLite demo DB. "
            "Each object must match WardrobeItem fields."
        ),
    )
    clean_item_ids: list[str] = Field(
        default_factory=list,
        description="Convenience list of available item_ids surfaced in wardrobe_items.",
    )
    wardrobe_summary: str = Field(
        default="",
        description=(
            "Bullet or sentence summary describing coverage by category/formality/"
            "warmth plus any fallback logic."
        ),
    )
    missing_categories: list[str] = Field(default_factory=list)
    notes: Optional[str] = Field(
        default=None,
        description="Optional clarifying details (e.g., why recently worn items were reused).",
    )


INSTRUCTION = """You are the FreshFit Wardrobe Cataloger.

Workflow:
1. When `items` is empty, call `demo_wardrobe_tool` to pull the latest closet snapshot from the SQLite DB. Always pass `user_id` and set `categories=required_categories` when provided.
2. Normalize tool output into the WardrobeItem schema (item_id, name, category, color, warmth_level, formality, body_zone, last_worn_date). These fields must mirror the DB columns exactly—do not invent extra attributes.
3. Remove any entries whose `item_id` appears in `banned_items`. For rotation, prefer items whose `last_worn_date` is at least 2 days old; only reuse more recent pieces if covering `required_categories` demands it, and explain that decision in `notes`.
4. Populate `wardrobe_items` with the filtered objects and set `clean_item_ids` to the list of their IDs. Cover all `required_categories`; if you cannot satisfy a category, add it to `missing_categories`.
5. Compose `wardrobe_summary` as concise prose or bullet text describing category coverage, warmth/formality balance, and notable recency gaps so downstream agents can reference it verbatim.
6. Use `notes` to mention exceptional handling (e.g., "Reusing dark denim worn yesterday because no other clean bottoms available").

Return JSON that strictly follows WardrobeCatalogerOutput."""


def wardrobe_cataloger_agent() -> Agent:
    """Construct the Wardrobe Cataloger agent."""

    return Agent(
        name="wardrobe_cataloger",
        description="Filters wardrobe items to produce a candidate pool.",
        instruction=INSTRUCTION,
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        input_schema=WardrobeCatalogerInput,
        output_schema=WardrobeCatalogerOutput,
        output_key='wardrobe_items',
        tools=[demo_wardrobe_tool],
    )

