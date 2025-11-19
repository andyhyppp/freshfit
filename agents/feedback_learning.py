"""Feedback & Learning agent."""

from typing import Literal, Optional

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


class FeedbackEvent(BaseModel):
    """Single feedback interaction from the user."""

    outfit_id: str
    decision: Literal["accepted", "rejected", "skipped"]
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    tags: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
    future_intent: Literal[
        "try_again", "maybe_later", "do_not_recommend"
    ] = Field(
        default="maybe_later",
        description=(
            "Signals whether the user wants to see this outfit (or a variant) again, "
            "is unsure, or wants it filtered from future slates."
        ),
    )


class FeedbackLearningInput(BaseModel):
    """Payload passed into the Feedback & Learning agent."""

    events: list[FeedbackEvent]
    presented_outfits: list[str] = Field(
        default_factory=list,
        description=(
            "Optional ordered descriptions of the outfits just shown so the agent "
            "can reference them while prompting the user."
        ),
    )


class OutfitFeedbackRecord(BaseModel):
    """Normalized per-outfit feedback summary."""

    outfit_id: str
    decision: Literal["accepted", "rejected", "skipped"]
    was_selected: bool = Field(
        default=False,
        description="True when this outfit was the user's primary selection.",
    )
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    future_intent: Literal["try_again", "maybe_later", "do_not_recommend"] = (
        "maybe_later"
    )
    tags: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class MetricsLogEvent(BaseModel):
    """Structured payloads destined for the Metrics agent."""

    event_type: Literal["selection", "rating", "preference_update"]
    outfit_id: str
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    future_intent: Optional[str] = None
    notes: Optional[str] = None


class FeedbackLearningOutput(BaseModel):
    """Summary describing updates applied."""

    acknowledgements: list[str] = Field(default_factory=list)
    next_actions: Optional[str] = None
    selection_prompt: str = Field(
        default=(
            "Which outfit_id are you choosing? Reply with the id so I can log it "
            "and refresh your wardrobe rotation."
        ),
        description="User-facing CTA for locking in a single outfit.",
    )
    rating_prompt: str = Field(
        default=(
            "Please rate every outfit from 1-5 stars and tag whether you'd like to "
            "see it again (`try_again`), are unsure (`maybe_later`), or never want "
            "it recommended again (`do_not_recommend`)."
        ),
        description="Guidance for capturing slate-wide ratings and future intent.",
    )
    selected_outfit_id: Optional[str] = Field(
        default=None,
        description="Outfit_id the user ultimately selected for wear.",
    )
    outfit_feedback: list[OutfitFeedbackRecord] = Field(
        default_factory=list,
        description="Per-outfit normalized feedback, covering decisions and ratings.",
    )
    metrics_events: list[MetricsLogEvent] = Field(
        default_factory=list,
        description=(
            "Log-ready events (selection + ratings) that downstream Metrics agent "
            "can ingest."
        ),
    )


INSTRUCTION = """You are the FreshFit Feedback & Learning agent.
- Interpret the latest outfit decisions, ratings, and tags.
- Produce acknowledgements plus any preference or banned-combo updates needed.
- Start by confirming which outfit was selected; use `selection_prompt` to guide the user when the decision is missing, and store the response in `selected_outfit_id`.
- Immediately follow up with `rating_prompt`, collecting a 1–5 star score and `future_intent` (`try_again`, `maybe_later`, `do_not_recommend`) for every outfit in the slate so we know whether to resurface them.
- Populate `outfit_feedback` with one entry per outfit, echoing the decision, rating, tags, notes, and whether it was selected.
- For each selection or rating captured, emit a corresponding `metrics_events` entry so the Metrics agent can record acceptance rate and preference deltas.
- Highlight if downstream agents need to refresh cached preference features or banned combos based on the new intel.
Return JSON that matches FeedbackLearningOutput."""


def feedback_learning_agent() -> Agent:
    """Construct the Feedback & Learning agent."""

    return Agent(
        name="feedback_learning",
        description="Processes user feedback, ratings, and 'never again' directives.",
        instruction=INSTRUCTION,
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        input_schema=FeedbackLearningInput,
        output_schema=FeedbackLearningOutput,
    )

