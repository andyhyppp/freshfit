"""Preference history FunctionTool for FreshFit agents."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Optional

from google.adk.tools.function_tool import FunctionTool

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "demo_preferences.db"


def _serialize_outfit_row(row: sqlite3.Row) -> dict[str, Any]:
    """Normalize outfit_feedback rows."""

    tags = row["tags"].split(",") if row["tags"] else []
    return {
        "outfit_id": row["outfit_id"],
        "outfit_name": row["outfit_name"],
        "decision": row["decision"],
        "rating": row["rating"],
        "future_intent": row["future_intent"],
        "notes": row["notes"],
        "tags": tags,
        "created_at": row["created_at"],
        "outfit_description": row["outfit_description"],
    }


def _serialize_item_row(row: sqlite3.Row) -> dict[str, Any]:
    """Normalize item_feedback rows."""

    return {
        "item_id": row["item_id"],
        "item_short_name": row["item_short_name"],
        "outfit_id": row["outfit_id"],
        "decision": row["decision"],
        "rating": row["rating"],
        "future_intent": row["future_intent"],
        "notes": row["notes"],
        "created_at": row["created_at"],
    }


def fetch_preference_history(
    user_id: str = "123",
    *,
    liked_rating_min: int = 4,
    disliked_rating_max: int = 1,
    limit: Optional[int] = None,
) -> dict[str, Any]:
    """Return liked/disliked outfits and items from the demo preference DB.

    Args:
        user_id: Demo user identifier to filter feedback rows.
        liked_rating_min: Inclusive lower bound for liked outfits/items.
        disliked_rating_max: Inclusive upper bound for disliked outfits/items.
        limit: Optional per-bucket limit (applied independently to liked/disliked results).

    Returns:
        Dict containing liked/disliked outfits and items keyed by rating buckets.
    """

    if liked_rating_min < 1 or liked_rating_min > 5:
        raise ValueError("liked_rating_min must be between 1 and 5.")
    if disliked_rating_max < 1 or disliked_rating_max > liked_rating_min:
        raise ValueError("disliked_rating_max must be between 1 and liked_rating_min.")
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Demo preference database not found at {DB_PATH}. "
            "Run scripts/create_preference_db.py first."
        )

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        outfit_limit_clause = " LIMIT ?" if limit else ""
        outfit_limit_params: list[Any] = [limit] if limit else []

        liked_outfit_rows = conn.execute(
            f"""
            SELECT
                outfit_id,
                outfit_name,
                outfit_description,
                decision,
                rating,
                future_intent,
                notes,
                tags,
                created_at
            FROM outfit_feedback
            WHERE user_id = ?
              AND rating IS NOT NULL
              AND rating >= ?
            ORDER BY created_at DESC{outfit_limit_clause}
            """,
            [user_id, liked_rating_min, *outfit_limit_params],
        ).fetchall()

        disliked_outfit_rows = conn.execute(
            f"""
            SELECT
                outfit_id,
                outfit_name,
                outfit_description,
                decision,
                rating,
                future_intent,
                notes,
                tags,
                created_at
            FROM outfit_feedback
            WHERE user_id = ?
              AND rating IS NOT NULL
              AND rating <= ?
            ORDER BY created_at DESC{outfit_limit_clause}
            """,
            [user_id, disliked_rating_max, *outfit_limit_params],
        ).fetchall()

        item_limit_clause = " LIMIT ?" if limit else ""
        item_limit_params: list[Any] = [limit] if limit else []

        liked_item_rows = conn.execute(
            f"""
            SELECT
                item_id,
                item_short_name,
                outfit_id,
                decision,
                rating,
                future_intent,
                notes,
                created_at
            FROM item_feedback
            WHERE user_id = ?
              AND rating IS NOT NULL
              AND rating >= ?
            ORDER BY created_at DESC{item_limit_clause}
            """,
            [user_id, liked_rating_min, *item_limit_params],
        ).fetchall()

        disliked_item_rows = conn.execute(
            f"""
            SELECT
                item_id,
                item_short_name,
                outfit_id,
                decision,
                rating,
                future_intent,
                notes,
                created_at
            FROM item_feedback
            WHERE user_id = ?
              AND rating IS NOT NULL
              AND rating <= ?
            ORDER BY created_at DESC{item_limit_clause}
            """,
            [user_id, disliked_rating_max, *item_limit_params],
        ).fetchall()

    return {
        "user_id": user_id,
        "liked_outfits": [_serialize_outfit_row(row) for row in liked_outfit_rows],
        "disliked_outfits": [
            _serialize_outfit_row(row) for row in disliked_outfit_rows
        ],
        "liked_items": [_serialize_item_row(row) for row in liked_item_rows],
        "disliked_items": [_serialize_item_row(row) for row in disliked_item_rows],
        "metadata": {
            "liked_rating_min": liked_rating_min,
            "disliked_rating_max": disliked_rating_max,
            "limit": limit,
        },
    }


preference_history_tool = FunctionTool(fetch_preference_history)
