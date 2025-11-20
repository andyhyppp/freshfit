"""Utility FunctionTool for retrieving the current Pacific date."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from google.adk.tools.function_tool import FunctionTool

PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


def get_current_date(_: Optional[str] = None) -> dict[str, str]:
    """Return today's date (ISO-8601) assuming Pacific Time."""

    now = datetime.now(tz=PACIFIC_TZ)
    return {
        "date": now.strftime("%Y-%m-%d"),
        "iso_timestamp": now.isoformat(),
        "timezone": "America/Los_Angeles",
    }


date_tool = FunctionTool(get_current_date)

