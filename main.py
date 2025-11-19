import asyncio
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
    description="A sequential agent that combines the outputs of the outfit designer, explanation agent, and feedback learning agent.",
    sub_agents=[
        outfit_agent,
        # ranking_agent,
        explanation_agent_instance,
        feedback_agent,
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


async def main() -> None:
    
    runner = Runner(
        app_name=APP_NAME,
        agent=root_agent,
        session_service=session_service,
        memory_service=memory_service,
    )

    # Create a session
    session_id = "session_1"
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id
    )

    # Create a message content object
    message = types.Content(
        parts=[types.Part(text="what should I wear for a date in seattle on 2025-11-17")]
    )

    # Run the agent asynchronously and collect the final response
    final_response = None
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=message
    ):
        # Print events for debugging
        print(f"Event: {event}")
        # Capture the final response
        if hasattr(event, 'response'):
            final_response = event.response
    
    print("\n=== Final Response ===")
    print(final_response)


if __name__ == "__main__":
    asyncio.run(main())