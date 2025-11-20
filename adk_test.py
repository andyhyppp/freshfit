import asyncio
import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError(
        "GOOGLE_API_KEY not found in environment variables. Please set it in .env file"
    )

# Create a simple agent with Gemini model and Google Search
root_agent = Agent(
    name="helpful_assistant",
    model=Gemini(model="gemini-2.5-flash-lite", api_key=api_key),
    description="A simple agent that can answer questions.",
    instruction="You are a helpful assistant. Use Google Search when needed.",
    tools=[google_search],
)


async def main():
    # Create a runner and execute a test query
    runner = Runner(
        app_name="helpful_assistant",
        agent=root_agent,
        session_service=InMemorySessionService(),
    )
    response = await runner.run_debug("what is weather in kirkland on 2025-11-17")

    # Print the response
    print("\n=== Response ===")
    print(response)


# Run the async function
if __name__ == "__main__":
    asyncio.run(main())
