from typing import Literal, Optional

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types
from pydantic import BaseModel, Field

from tools.demo_wardrobe_tool import (
    add_wardrobe_tool,
    delete_wardrobe_tool,
    demo_wardrobe_tool,
)

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)


# --- Cloth Adder Agent ---

ADDER_INSTRUCTION = """You are the FreshFit Cloth Adder agent.

Task:
1. Analyze the user's input (text and/or image).
2. Extract wardrobe item details (name, category, color, warmth_level, formality, body_zone).
   - Infer missing details from the image if provided.
   - If no image is provided, rely on the text description.
   - Default `user_id` to "123" if not specified.
   - `last_worn_date` can be left null unless specified.
   - Ensure `category` is one of: [top, bottom, dress, outerwear, shoes, accessory]
   - Ensure `warmth_level` is one of: [light, medium, heavy]
   - Ensure `formality` is one of: [casual, smart_casual, business, formal]
   - Ensure `body_zone` is one of: [upper, lower, full_body, shoe, accessory]
3. Call `add_wardrobe_tool` with the extracted fields.
4. Confirm the addition to the user with the new item name and ID.

Output:
Return a natural language confirmation.
"""


class WardrobeItemInput(BaseModel):
    """Schema for wardrobe item addition."""

    user_id: str = Field(default="123", description="User ID owning the item.")
    name: str = Field(..., description="Short descriptive name of the item.")
    category: Literal["top", "bottom", "dress", "outerwear", "shoes", "accessory"] = (
        Field(..., description="Category of the item.")
    )
    color: str = Field(default="unknown", description="Primary color.")
    warmth_level: Literal["light", "medium", "heavy"] = Field(
        default="medium", description="Warmth level."
    )
    formality: Literal["casual", "smart_casual", "business", "formal"] = Field(
        default="casual", description="Formality level."
    )
    body_zone: Literal["upper", "lower", "full_body", "shoe", "accessory"] = Field(
        default="upper", description="Body zone."
    )
    last_worn_date: Optional[str] = Field(
        default=None, description="Last worn date (ISO)."
    )


def cloth_adder_agent() -> Agent:
    return Agent(
        name="cloth_adder",
        description="Adds a new cloth item to the wardrobe from text or image.",
        instruction=ADDER_INSTRUCTION,
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        tools=[add_wardrobe_tool],
        input_schema=WardrobeItemInput,
    )


# --- Cloth Deleter Agent ---

DELETER_INSTRUCTION = """You are the FreshFit Cloth Deleter agent.

Task:
1. Identify which item(s) the user wants to delete.
2. If the user provides a name or description but not an ID:
   - Call `demo_wardrobe_tool` (fetch) to find matching items.
   - If multiple matches are found, ask for clarification (or list them).
   - If one match is found, proceed.
3. Call `delete_wardrobe_tool` with the `item_id`.
4. Confirm the deletion to the user.

Output:
Return a natural language confirmation.
"""


def cloth_deleter_agent() -> Agent:
    return Agent(
        name="cloth_deleter",
        description="Deletes a cloth item from the wardrobe by ID or description.",
        instruction=DELETER_INSTRUCTION,
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        tools=[demo_wardrobe_tool, delete_wardrobe_tool],
    )


# --- Cloth Registrar (Router) Agent ---

REGISTRAR_INSTRUCTION = """You are the FreshFit Cloth Registrar agent.

Task:
1. Analyze the user's request to determine if they want to ADD or DELETE a clothing item.
   - "Add": User uploads a photo or describes a new item to save.
   - "Delete": User wants to remove, discard, or delete an item.
2. Route the request to the appropriate sub-agent:
   - If adding: Delegate to `cloth_adder`.
   - If deleting: Delegate to `cloth_deleter`.
3. If the request is unclear, ask for clarification.

"""


def cloth_registrar_agent() -> Agent:
    adder = cloth_adder_agent()
    deleter = cloth_deleter_agent()

    return Agent(
        name="cloth_registrar",
        description="Manages wardrobe additions and deletions.",
        instruction=REGISTRAR_INSTRUCTION,
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        sub_agents=[adder, deleter],
    )
