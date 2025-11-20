import asyncio
import json
from typing import Any, Optional

from dotenv import load_dotenv
from google.adk.agents import ParallelAgent, SequentialAgent
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.feedback_learning import feedback_learning_agent
from agents.outfit_designer import outfit_designer_agent
from agents.preference_ranking import preference_ranking_agent
from agents.weather_agent import weather_agent
from agents.wardrobe_cataloger import wardrobe_cataloger_agent
from agents.explanation_agent import explanation_agent

load_dotenv()


APP_NAME = "FreshFit"
USER_ID = "123"  # for demo purposes, just use a random id


class FreshFitRootAgent(SequentialAgent):
    """Thin subclass so ADK infers the correct app origin."""


weather_agent_instance = weather_agent()
wardrobe_agent = wardrobe_cataloger_agent()
outfit_agent = outfit_designer_agent()
explanation_agent_instance = explanation_agent()
feedback_agent = feedback_learning_agent()
ranking_agent = preference_ranking_agent()

parallel_agent = ParallelAgent(
    name="ParallelAgents",
    description="Runs the weather agent and wardrobe cataloger in parallel.",
    sub_agents=[
        weather_agent_instance,
        wardrobe_agent,
    ],
)

sequential_agent = SequentialAgent(
    name="SequentialAgents",
    description=(
        "A sequential agent that combines the outputs of the outfit designer and "
        "explanation agent. Feedback is handled interactively via the CLI."
    ),
    sub_agents=[
        outfit_agent,
        ranking_agent,
        explanation_agent_instance,
    ],
)


root_agent = FreshFitRootAgent(
    name=APP_NAME,
    sub_agents=[
        parallel_agent,
        sequential_agent,
    ],
)


memory_service = InMemoryMemoryService()
session_service = InMemorySessionService()


def _content_to_text(content: Optional[types.Content]) -> Optional[str]:
    if content is None:
        return None
    parts = []
    for part in content.parts:
        if getattr(part, "text", None):
            parts.append(part.text)
    return "\n".join(parts) if parts else None


def _parse_outfit_payload(
    outfit_text: Optional[str],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Decode the outfit designer payload for downstream CLI helpers."""

    if not outfit_text:
        return [], {}

    try:
        payload = json.loads(outfit_text)
    except json.JSONDecodeError:
        return [], {}

    outfits = payload.get("outfits") or []
    lookup: dict[str, dict[str, Any]] = {}
    for entry in outfits:
        outfit_id = entry.get("outfit_id")
        if outfit_id:
            lookup[outfit_id] = entry
    return outfits, lookup


def _display_outfit_menu(indexed_outfits: list[tuple[int, dict[str, Any]]]) -> None:
    if not indexed_outfits:
        return

    print("\nOutfit Options (use the number to select or rate):")
    for index, outfit in indexed_outfits:
        outfit_id = outfit.get("outfit_id", "unknown")
        name = outfit.get("outfit_name", "Unnamed Look")
        print(f"  {index}. {outfit_id} - {name}")


def _prompt_index_choice(
    max_index: int,
    prompt: str,
    *,
    allow_blank: bool = False,
) -> Optional[int]:
    if max_index <= 0:
        return None

    while True:
        raw = input(prompt).strip()
        if allow_blank and not raw:
            return None
        if raw.isdigit():
            value = int(raw)
            if 1 <= value <= max_index:
                return value
        print(
            f"Please enter a number between 1 and {max_index}, or press Enter to skip."
        )


async def run_agent_turn(
    runner: Runner,
    *,
    session_id: str,
    user_text: str,
) -> tuple[Optional[str], Optional[str]]:
    """Send a single user turn through the orchestrated agent graph."""

    message = types.Content(parts=[types.Part(text=user_text)])
    final_response: Optional[str] = None
    explanation_snapshot: Optional[str] = None
    outfit_snapshot: Optional[str] = None

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=message,
    ):
        # Print each event for visibility/debugging.
        print(f"\n[Agent Event] {event}")

        if hasattr(event, "response") and event.response:
            final_response = event.response
            continue

        event_text = _content_to_text(getattr(event, "content", None))
        if not event_text:
            continue

        # Keep the last textual event as a fallback response.
        final_response = event_text

        # Capture the explanation agent payload so we can always show the slate.
        if getattr(event, "author", None) == outfit_agent.name:
            outfit_snapshot = event_text
        if getattr(event, "author", None) == explanation_agent_instance.name:
            explanation_snapshot = event_text

    if final_response is None:
        final_response = explanation_snapshot

    if final_response:
        print("\nFreshFit:\n")
        print(final_response)

    return final_response, outfit_snapshot


async def collect_feedback_from_user(
    explanations_response: str | None,
    outfits: list[dict[str, Any]] | None = None,
) -> tuple[str, list[dict[str, str]]]:
    """Prompt the user to pick an outfit and to rate each one in the slate."""

    if explanations_response:
        print("\n--- Outfit Slate ---")
        print(explanations_response)

    indexed_outfits = list(enumerate(outfits or [], start=1))
    if indexed_outfits:
        _display_outfit_menu(indexed_outfits)
        selection_index = _prompt_index_choice(
            len(indexed_outfits),
            "\nEnter the number of the outfit you want to wear (press Enter to skip): ",
            allow_blank=True,
        )
        selected_outfit = (
            indexed_outfits[selection_index - 1][1]["outfit_id"]
            if selection_index
            else "skip"
        )
    else:
        selected_outfit = (
            input("\nEnter the outfit_id you want to wear (or type 'skip'): ").strip()
            or "skip"
        )

    ratings: list[dict[str, str]] = []
    print(
        "\nNow rate each outfit you saw. When finished, press Enter without choosing a number."
    )
    while True:
        if indexed_outfits:
            rating_index = _prompt_index_choice(
                len(indexed_outfits),
                "  Outfit number (blank to finish): ",
                allow_blank=True,
            )
            if rating_index is None:
                break
            outfit_id = indexed_outfits[rating_index - 1][1]["outfit_id"]
        else:
            outfit_id = input("  Outfit ID (blank to finish): ").strip()
            if not outfit_id:
                break
        rating = input("  Rating 1-5 (blank if n/a): ").strip()
        intent = input(
            "  Future intent [try_again/maybe_later/do_not_recommend]: "
        ).strip()
        notes = input("  Notes or tags: ").strip()
        ratings.append(
            {
                "outfit_id": outfit_id,
                "rating": rating,
                "future_intent": intent or "maybe_later",
                "notes": notes,
            }
        )

    return selected_outfit, ratings


async def main() -> None:
    suggestion_runner = Runner(
        app_name=APP_NAME,
        agent=root_agent,
        session_service=session_service,
        memory_service=memory_service,
    )
    feedback_runner = Runner(
        app_name=f"{APP_NAME}_Feedback",
        agent=feedback_agent,
        session_service=session_service,
        memory_service=memory_service,
    )

    suggestion_session_id = "session_slate_1"
    feedback_session_id = "session_feedback_1"
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=suggestion_session_id,
    )
    await session_service.create_session(
        app_name=f"{APP_NAME}_Feedback",
        user_id=USER_ID,
        session_id=feedback_session_id,
    )

    print(
        "FreshFit CLI\n"
        "- Ask for outfit ideas, then respond with the requested selection/ratings.\n"
        "- Type 'exit' or 'quit' to stop."
    )

    while True:
        user_text = input("\nYou: ").strip()
        if not user_text:
            continue
        if user_text.lower() in {"exit", "quit"}:
            print("Ending FreshFit session. See you next time!")
            break

        response, outfit_snapshot = await run_agent_turn(
            suggestion_runner,
            session_id=suggestion_session_id,
            user_text=user_text,
        )

        outfits, outfit_lookup = _parse_outfit_payload(outfit_snapshot)

        if response is None:
            continue

        # Collect structured feedback and send it to the Feedback & Learning agent.
        selection, ratings = await collect_feedback_from_user(
            response,
            outfits,
        )
        if not ratings and selection.lower() == "skip":
            print("No selection or ratings captured; skipping the feedback agent call.")
            continue

        feedback_events: list[dict[str, object]] = []
        valid_intents = {"try_again", "maybe_later", "do_not_recommend"}
        for rating_entry in ratings:
            try:
                rating_value = (
                    int(rating_entry["rating"]) if rating_entry["rating"] else None
                )
            except ValueError:
                rating_value = None

            intent_value = rating_entry["future_intent"].lower()
            if intent_value not in valid_intents:
                intent_value = "maybe_later"

            feedback_events.append(
                {
                    "outfit_id": rating_entry["outfit_id"],
                    "decision": (
                        "accepted"
                        if rating_entry["outfit_id"] == selection
                        else "rejected"
                    ),
                    "rating": rating_value,
                    "future_intent": intent_value,
                    "notes": rating_entry["notes"] or None,
                    "tags": [],
                }
            )

        if selection.lower() != "skip" and not any(
            entry["outfit_id"] == selection for entry in feedback_events
        ):
            feedback_events.append(
                {
                    "outfit_id": selection,
                    "decision": "accepted",
                    "rating": None,
                    "future_intent": "try_again",
                    "notes": None,
                    "tags": [],
                }
            )

        feedback_payload = {
            "events": feedback_events,
            "presented_outfits": [str(response)],
        }

        if feedback_events:
            record_feedback_events(USER_ID, feedback_events, outfit_lookup)

        await run_agent_turn(
            feedback_runner,
            session_id=feedback_session_id,
            user_text=json.dumps(feedback_payload, indent=2),
        )


if __name__ == "__main__":
    asyncio.run(main())
