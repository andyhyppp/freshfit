"""Demo wardrobe DB tool for FreshFit agents."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any
from typing import Optional

from google.adk.tools.function_tool import FunctionTool

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "demo_wardrobe.db"


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "item_id": str(row["item_id"]),
        "user_id": row["user_id"],
        "name": row["name"],
        "category": row["category"],
        "color": row["color"],
        "warmth_level": row["warmth_level"],
        "formality": row["formality"],
        "body_zone": row["body_zone"],
        "last_worn_date": row["last_worn_date"],
    }


def fetch_demo_wardrobe_items(
    user_id: str = "123",
    categories: Optional[list[str]] = None,
    limit: Optional[int] = None,
) -> dict[str, Any]:
    """Return wardrobe entries from the demo SQLite database.

    Args:
        user_id: Demo user identifier to filter wardrobe rows.
        categories: Optional list of category names to filter (e.g., ["top", "shoes"]).
        limit: Optional row limit for the response.

    Returns:
        Dict containing an `items` list with wardrobe item dicts.
    """

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Demo wardrobe database not found at {DB_PATH}. "
            "Run scripts/create_demo_wardrobe_db.py first."
        )

    query = """
        SELECT
            item_id,
            user_id,
            name,
            category,
            color,
            warmth_level,
            formality,
            body_zone,
            last_worn_date
        FROM wardrobe_items
        WHERE user_id = ?
    """
    params: list[Any] = [user_id]
    params: list[Any] = [user_id]

    if categories:
        placeholders = ",".join("?" for _ in categories)
        query += f" AND category IN ({placeholders})"
        params.extend(categories)

    query += " ORDER BY category, name"

    if limit:
        query += " LIMIT ?"
        params.append(limit)

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()

    return {"items": [_row_to_dict(row) for row in rows]}


demo_wardrobe_tool = FunctionTool(fetch_demo_wardrobe_items)

