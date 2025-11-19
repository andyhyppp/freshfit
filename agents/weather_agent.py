"""Weather agent responsible for contextual weather capture."""

from typing import Literal, Optional

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.tools.google_search_agent_tool import (
    GoogleSearchAgentTool,
    create_google_search_agent,
)
from google.genai import types
from pydantic import BaseModel, Field, field_validator


TEMP_BUCKETS = ("cold", "cool", "mild", "warm", "hot")

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

class WeatherRequest(BaseModel):
    """Minimal weather query payload passed to tools."""

    location: str
    date: str
    units: Literal["metric", "imperial"] = "metric"


class WeatherAgentInput(BaseModel):
    """Structured inputs coming from the Orchestrator."""

    location: str = Field(..., description="City or geo lookup for weather APIs.")
    date: str = Field(..., description="ISO date for the requested day.")
    occasion_tag: str = Field(..., description="User-provided or calendar tag.")
    dress_code: Optional[str] = None


class WeatherAgentOutput(BaseModel):
    """Normalized context emitted to downstream agents."""

    location: str
    date: str
    temp_bucket: Literal[TEMP_BUCKETS]
    average_temp_c: Optional[float] = None
    high_temp_c: Optional[float] = None
    low_temp_c: Optional[float] = None
    precipitation_chance: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    @field_validator("temp_bucket")
    def _validate_bucket(cls, bucket: str) -> str:  # noqa: D401
        """Ensure temp bucket belongs to the supported set."""
        if bucket not in TEMP_BUCKETS:
            raise ValueError(f"temp_bucket must be one of {TEMP_BUCKETS}")
        return bucket



INSTRUCTION = """You are the FreshFit Weather agent that feeds the daily intake flow.

Input payload:
- location: user city or geo lookup
- date: ISO date (local to the user)
- occasion_tag & optional dress_code hints

Task:
1. Use the google_search tool to fetch weather for the exact location/date in Celsius (average, high, low, precipitation chance). Prefer day-level summaries; if nothing is available, state that you reused the closest recent data.
2. Map the average temperature into the required bucket:
   cold <10°C, cool 10-18°C, mild 18-24°C, warm 24-30°C, hot >30°C.
3. Populate precipitation_chance as a float between 0 and 1 (e.g., 40% → 0.4). If precipitation data is missing, output null.
4. Carry through the provided dress_code if present; otherwise infer a short recommendation aligned with the occasion_tag (e.g., "smart casual", "daily casual").
5. If you had to fall back to stale data or assumptions, mention it in a brief note inside the dress_code string.

Output:
- Return JSON that strictly matches WeatherAgentOutput. Do not add extra keys or prose. Example:
  {
    "location": "Seattle, WA",
    "date": "2025-02-10",
    "temp_bucket": "cool",
    "average_temp_c": 12.0,
    "high_temp_c": 15.0,
    "low_temp_c": 8.0,
    "precipitation_chance": 0.45
  }"""


def weather_agent() -> Agent:
    """Construct the FreshFit Weather agent."""

    # Wrap the built-in Google Search tool so it can be used alongside AFC.
    search_agent = create_google_search_agent(model="gemini-2.5-flash")
    search_tool = GoogleSearchAgentTool(search_agent)

    return Agent(
        name="weather_agent",
        description="Collects weather and occasion metadata for FreshFit.",
        instruction=INSTRUCTION,
        # input_schema=WeatherAgentInput,
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        output_key="weather",
        tools=[search_tool],
    )

