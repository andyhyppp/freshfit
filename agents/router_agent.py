from typing import List

from google.adk.agents import Agent, ParallelAgent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.genai import types

from agents.cloth_registrar import cloth_registrar_agent
from agents.explanation_agent import explanation_agent
from agents.outfit_designer import outfit_designer_agent
from agents.preference_ranking import preference_ranking_agent
from agents.wardrobe_cataloger import wardrobe_cataloger_agent
from agents.weather_agent import weather_agent

APP_NAME = "FreshFit"

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)


class OutfitFlowAgent(SequentialAgent):
    """Sequential agent for outfit recommendations."""


class FreshFitRouter(Agent):
    """Root router for FreshFit."""


def create_freshfit_router() -> Agent:
    """Constructs the main FreshFit router agent with all sub-agents."""

    # Instantiate leaf agents
    weather = weather_agent()
    wardrobe = wardrobe_cataloger_agent()
    outfit = outfit_designer_agent()
    ranking = preference_ranking_agent()
    explanation = explanation_agent()
    registrar = cloth_registrar_agent()

    # Parallel branch: fetch context
    parallel_agent = ParallelAgent(
        name="ParallelAgents",
        description="Runs the weather agent and wardrobe cataloger in parallel.",
        sub_agents=[weather, wardrobe],
    )

    # Sequential branch: generate and explain
    sequential_agent = SequentialAgent(
        name="SequentialAgents",
        description=(
            "A sequential agent that combines the outputs of the outfit designer and "
            "explanation agent. Feedback is handled interactively via the CLI."
        ),
        sub_agents=[outfit, ranking, explanation],
    )

    # Outfit Flow: combines parallel and sequential
    outfit_flow = OutfitFlowAgent(
        name="OutfitFlow",
        description="Generates outfit recommendations.",
        sub_agents=[parallel_agent, sequential_agent],
    )

    # Root Router
    root_agent = FreshFitRouter(
        name=APP_NAME,
        description="Router for FreshFit.",
        instruction=(
            "You are the FreshFit router. Your goal is to help the user with their "
            "wardrobe and outfit needs.\n"
            "If the user wants outfit recommendations, to dress for the weather, or "
            "general styling advice, route them to `OutfitFlow`.\n"
            "If the user wants to add clothes, delete items, or manage their wardrobe "
            "inventory, route them to `cloth_registrar`.\n"
            "If the request is unclear, ask for clarification."
        ),
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        sub_agents=[outfit_flow, registrar],
    )

    return root_agent
