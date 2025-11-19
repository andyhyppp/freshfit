import asyncio
import json
from dotenv import load_dotenv
from google.adk.agents import ParallelAgent, SequentialAgent
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from agents.weather_agent import weather_agent
from agents.wardrobe_cataloger import wardrobe_cataloger_agent
from agents.outfit_designer import outfit_designer_agent
from agents.explanation_agent import explanation_agent
from agents.feedback_learning import feedback_learning_agent
from agents.preference_ranking import preference_ranking_agent

load_dotenv()


APP_NAME = "FreshFitAgents"
USER_ID = "123"




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
        # ranking_agent,
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


async def run_agent_turn(
    runner: Runner,
    *,
    session_id: str,
    user_text: str,
) -> str | None:
    """Send a single user turn through the orchestrated agent graph."""

    message = types.Content(parts=[types.Part(text=user_text)])
    final_response = None

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=message,
    ):
        # Print each event for visibility/debugging.
        print(f"\n[Agent Event] {event}")
        if hasattr(event, "response"):
            final_response = event.response

    if final_response is not None:
        print("\nFreshFit:\n")
        print(final_response)

    return final_response


async def collect_feedback_from_user(
    explanations_response: str | None,
) -> tuple[str, list[dict[str, str]]]:
    """Prompt the user to pick an outfit and to rate each one in the slate."""

    if explanations_response:
        print("\n--- Outfit Slate ---")
        print(explanations_response)

    selected_outfit = input(
        "\nEnter the outfit_id you want to wear (or type 'skip'): "
    ).strip()
    if not selected_outfit:
        selected_outfit = "skip"

    ratings: list[dict[str, str]] = []
    print(
        "\nNow rate each outfit you saw. When finished, leave outfit_id empty to stop."
    )
    while True:
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

        response = await run_agent_turn(
            suggestion_runner,
            session_id=suggestion_session_id,
            user_text=user_text,
        )

        if response is None:
            continue

        # Collect structured feedback and send it to the Feedback & Learning agent.
        selection, ratings = await collect_feedback_from_user(response)
        if not ratings and selection.lower() == "skip":
            print(
                "No selection or ratings captured; skipping the feedback agent call."
            )
            continue

        feedback_events: list[dict[str, object]] = []
        valid_intents = {"try_again", "maybe_later", "do_not_recommend"}
        for rating_entry in ratings:
            try:
                rating_value = (
                    int(rating_entry["rating"])
                    if rating_entry["rating"]
                    else None
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

        await run_agent_turn(
            feedback_runner,
            session_id=feedback_session_id,
            user_text=json.dumps(feedback_payload, indent=2),
        )


if __name__ == "__main__":
    asyncio.run(main())