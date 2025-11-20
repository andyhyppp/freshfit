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


def add_wardrobe_item(
    user_id: str,
    name: str,
    category: str,
    color: str = "unknown",
    warmth_level: str = "medium",
    formality: str = "casual",
    body_zone: str = "upper",
    last_worn_date: Optional[str] = None,
) -> dict[str, Any]:
    """Add a new item to the wardrobe database.

    Args:
        user_id: The owner of the item.
        name: Short description of the item.
        category: One of [top, bottom, dress, outerwear, shoes, accessory].
        color: Primary color.
        warmth_level: [light, medium, heavy].
        formality: [casual, smart_casual, business, formal].
        body_zone: [upper, lower, full_body, shoe, accessory].
        last_worn_date: Optional ISO date string.

    Returns:
        Confirmation dict with the new item_id.
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DB not found at {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO wardrobe_items (
                user_id, name, category, color, warmth_level,
                formality, body_zone, last_worn_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                name,
                category,
                color,
                warmth_level,
                formality,
                body_zone,
                last_worn_date,
            ),
        )
        new_id = cursor.lastrowid

    return {"status": "success", "item_id": str(new_id), "name": name}


def delete_wardrobe_item(item_id: str) -> dict[str, Any]:
    """Delete an item from the wardrobe database by ID.

    Args:
        item_id: The unique ID of the item to remove.

    Returns:
        Success or error message.
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DB not found at {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "DELETE FROM wardrobe_items WHERE item_id = ?", (item_id,)
        )
        deleted_count = cursor.rowcount

    if deleted_count == 0:
        return {"status": "error", "message": f"Item {item_id} not found."}
    return {"status": "success", "message": f"Item {item_id} deleted."}


demo_wardrobe_tool = FunctionTool(fetch_demo_wardrobe_items)
add_wardrobe_tool = FunctionTool(add_wardrobe_item)
delete_wardrobe_tool = FunctionTool(delete_wardrobe_item)
