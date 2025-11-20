#!/usr/bin/env python3
"""Seed the demo preference SQLite DB for FreshFit user 123."""

from __future__ import annotations

import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "demo_preferences.db"
USER_ID = "123"

DEMO_OUTFITS = [
    {
        "outfit_id": "123-01",
        "outfit_name": "Cozy Business Casual",
        "outfit_description": (
            "Powder blue shirt, espresso wool trousers, and burgundy wingtips "
            "keep things polished for chilly drizzle."
        ),
        "outfit_items": ["27", "28", "29"],
        "outfit_item_details": [
            {"item_id": "27", "short_name": "Powder Blue Poplin Shirt"},
            {"item_id": "28", "short_name": "Espresso Wool Trousers"},
            {"item_id": "29", "short_name": "Burgundy Wingtip Oxfords"},
        ],
    },
    {
        "outfit_id": "123-02",
        "outfit_name": "Relaxed Errand Layers",
        "outfit_description": (
            "White linen tee, dark denim, and white court sneakers for an easy errand loop."
        ),
        "outfit_items": ["21", "4", "9"],
        "outfit_item_details": [
            {"item_id": "21", "short_name": "White Linen Tee"},
            {"item_id": "4", "short_name": "Dark Wash Denim"},
            {"item_id": "9", "short_name": "White Court Sneakers"},
        ],
    },
]

DEMO_EVENTS = [
    {
        "outfit_id": "123-01",
        "decision": "accepted",
        "rating": 5,
        "future_intent": "try_again",
        "notes": "Great balance of warmth and polish.",
    },
    {
        "outfit_id": "123-02",
        "decision": "rejected",
        "rating": 1,
        "future_intent": "do_not_recommend",
        "notes": "Too casual for workday errands.",
    },
]


def reset_preference_db() -> None:
    """Drop and recreate the demo preference database schema."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(
            """
            CREATE TABLE outfit_feedback (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                outfit_id TEXT NOT NULL,
                outfit_name TEXT,
                outfit_description TEXT,
                decision TEXT NOT NULL CHECK (
                    decision IN ('accepted', 'rejected', 'skipped')
                ),
                rating INTEGER CHECK (rating BETWEEN 1 AND 5),
                future_intent TEXT CHECK (
                    future_intent IN ('try_again', 'maybe_later', 'do_not_recommend')
                ),
                notes TEXT,
                tags TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE item_feedback (
                item_feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                outfit_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                item_short_name TEXT,
                decision TEXT NOT NULL CHECK (
                    decision IN ('accepted', 'rejected', 'skipped')
                ),
                rating INTEGER CHECK (rating BETWEEN 1 AND 5),
                future_intent TEXT CHECK (
                    future_intent IN ('try_again', 'maybe_later', 'do_not_recommend')
                ),
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES outfit_feedback (event_id) ON DELETE CASCADE
            );
            """
        )


def seed_preferences() -> None:
    """Insert demo feedback rows for downstream ranking experiments."""

    outfit_lookup = {entry["outfit_id"]: entry for entry in DEMO_OUTFITS}

    with sqlite3.connect(DB_PATH) as conn:
        for event in DEMO_EVENTS:
            outfit = outfit_lookup.get(event["outfit_id"])
            if not outfit:
                raise KeyError(f"No outfit definition for {event['outfit_id']}")

            tags = event.get("tags")
            serialized_tags = ",".join(tags) if tags else None

            cursor = conn.execute(
                """
                INSERT INTO outfit_feedback (
                    user_id,
                    outfit_id,
                    outfit_name,
                    outfit_description,
                    decision,
                    rating,
                    future_intent,
                    notes,
                    tags
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    USER_ID,
                    outfit["outfit_id"],
                    outfit["outfit_name"],
                    outfit["outfit_description"],
                    event["decision"],
                    event["rating"],
                    event["future_intent"],
                    event.get("notes"),
                    serialized_tags,
                ),
            )
            event_id = cursor.lastrowid

            conn.executemany(
                """
                INSERT INTO item_feedback (
                    event_id,
                    user_id,
                    outfit_id,
                    item_id,
                    item_short_name,
                    decision,
                    rating,
                    future_intent,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        event_id,
                        USER_ID,
                        outfit["outfit_id"],
                        item["item_id"],
                        item["short_name"],
                        event["decision"],
                        event["rating"],
                        event["future_intent"],
                        event.get("notes"),
                    )
                    for item in outfit["outfit_item_details"]
                ],
            )

        outfit_count = conn.execute("SELECT COUNT(*) FROM outfit_feedback").fetchone()[
            0
        ]
        item_count = conn.execute("SELECT COUNT(*) FROM item_feedback").fetchone()[0]

    print(
        f"Seeded preference DB at {DB_PATH} "
        f"(outfit rows: {outfit_count}, item rows: {item_count})"
    )


def main() -> None:
    reset_preference_db()
    seed_preferences()


if __name__ == "__main__":
    main()
