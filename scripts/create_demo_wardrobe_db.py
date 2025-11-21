#!/usr/bin/env python3
"""Seed the demo wardrobe SQLite DB for FreshFit user 123."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "demo_wardrobe.db"
DEMO_USER_ID = "123"

WARDROBE_ITEMS: list[dict[str, str | int]] = [
    {
        "item_id": 1,
        "name": "Sky Oxford Shirt",
        "category": "top",
        "color": "sky blue",
        "warmth_level": "light",
        "formality": "smart_casual",
        "body_zone": "upper",
        "last_worn_date": "2025-01-05",
    },
    {
        "item_id": 2,
        "name": "Merino Crew Sweater",
        "category": "top",
        "color": "charcoal",
        "warmth_level": "medium",
        "formality": "business",
        "body_zone": "upper",
        "last_worn_date": "2024-12-28",
    },
    {
        "item_id": 3,
        "name": "Camel Chinos",
        "category": "bottom",
        "color": "camel",
        "warmth_level": "light",
        "formality": "smart_casual",
        "body_zone": "lower",
        "last_worn_date": "2025-01-02",
    },
    {
        "item_id": 4,
        "name": "Dark Wash Denim",
        "category": "bottom",
        "color": "indigo",
        "warmth_level": "medium",
        "formality": "casual",
        "body_zone": "lower",
        "last_worn_date": "2025-01-07",
    },
    {
        "item_id": 5,
        "name": "Navy Slip Dress",
        "category": "dress",
        "color": "navy",
        "warmth_level": "light",
        "formality": "smart_casual",
        "body_zone": "full_body",
        "last_worn_date": "2024-12-31",
    },
    {
        "item_id": 6,
        "name": "Washed Denim Jacket",
        "category": "outerwear",
        "color": "light blue",
        "warmth_level": "light",
        "formality": "casual",
        "body_zone": "upper",
        "last_worn_date": "2025-01-03",
    },
    {
        "item_id": 7,
        "name": "Camel Wool Coat",
        "category": "outerwear",
        "color": "camel",
        "warmth_level": "heavy",
        "formality": "business",
        "body_zone": "upper",
        "last_worn_date": "2024-12-20",
    },
    {
        "item_id": 8,
        "name": "Leather Loafers",
        "category": "shoes",
        "color": "espresso",
        "warmth_level": "light",
        "formality": "business",
        "body_zone": "shoe",
        "last_worn_date": "2025-01-04",
    },
    {
        "item_id": 9,
        "name": "White Court Sneakers",
        "category": "shoes",
        "color": "white",
        "warmth_level": "light",
        "formality": "casual",
        "body_zone": "shoe",
        "last_worn_date": "2025-01-06",
    },
    {
        "item_id": 10,
        "name": "Graphite Wool Scarf",
        "category": "accessory",
        "color": "graphite",
        "warmth_level": "medium",
        "formality": "smart_casual",
        "body_zone": "accessory",
        "last_worn_date": "2025-01-01",
    },
    {
        "item_id": 11,
        "name": "Olive Thermal Henley",
        "category": "top",
        "color": "olive",
        "warmth_level": "medium",
        "formality": "casual",
        "body_zone": "upper",
        "last_worn_date": "2024-12-30",
    },
    {
        "item_id": 12,
        "name": "Ivory Silk Blouse",
        "category": "top",
        "color": "ivory",
        "warmth_level": "light",
        "formality": "smart_casual",
        "body_zone": "upper",
        "last_worn_date": "2024-12-22",
    },
    {
        "item_id": 13,
        "name": "Black Ponte Pants",
        "category": "bottom",
        "color": "black",
        "warmth_level": "medium",
        "formality": "business",
        "body_zone": "lower",
        "last_worn_date": "2024-12-24",
    },
    {
        "item_id": 14,
        "name": "Rust Pleated Midi Skirt",
        "category": "bottom",
        "color": "rust",
        "warmth_level": "light",
        "formality": "smart_casual",
        "body_zone": "lower",
        "last_worn_date": "2024-12-19",
    },
    {
        "item_id": 15,
        "name": "Midnight Velvet Blazer",
        "category": "outerwear",
        "color": "midnight",
        "warmth_level": "medium",
        "formality": "smart_casual",
        "body_zone": "upper",
        "last_worn_date": "2024-12-18",
    },
    {
        "item_id": 16,
        "name": "Stormproof Trench",
        "category": "outerwear",
        "color": "stone",
        "warmth_level": "heavy",
        "formality": "business",
        "body_zone": "upper",
        "last_worn_date": "2024-12-15",
    },
    {
        "item_id": 17,
        "name": "Black Chelsea Boots",
        "category": "shoes",
        "color": "black",
        "warmth_level": "medium",
        "formality": "smart_casual",
        "body_zone": "shoe",
        "last_worn_date": "2025-01-03",
    },
    {
        "item_id": 18,
        "name": "Suede Ankle Boots",
        "category": "shoes",
        "color": "taupe",
        "warmth_level": "medium",
        "formality": "casual",
        "body_zone": "shoe",
        "last_worn_date": "2024-12-27",
    },
    {
        "item_id": 19,
        "name": "Gold Statement Necklace",
        "category": "accessory",
        "color": "gold",
        "warmth_level": "light",
        "formality": "smart_casual",
        "body_zone": "accessory",
        "last_worn_date": "2024-12-29",
    },
    {
        "item_id": 20,
        "name": "Leather Crossbody Bag",
        "category": "accessory",
        "color": "cognac",
        "warmth_level": "light",
        "formality": "casual",
        "body_zone": "accessory",
        "last_worn_date": "2025-01-02",
    },
    {
        "item_id": 21,
        "name": "White Linen Tee",
        "category": "top",
        "color": "white",
        "warmth_level": "light",
        "formality": "casual",
        "body_zone": "upper",
        "last_worn_date": "2024-12-26",
    },
    {
        "item_id": 22,
        "name": "Charcoal Tailored Trousers",
        "category": "bottom",
        "color": "charcoal",
        "warmth_level": "medium",
        "formality": "business",
        "body_zone": "lower",
        "last_worn_date": "2024-12-23",
    },
    {
        "item_id": 23,
        "name": "Tan City Sneakers",
        "category": "shoes",
        "color": "tan",
        "warmth_level": "light",
        "formality": "smart_casual",
        "body_zone": "shoe",
        "last_worn_date": "2024-12-25",
    },
    {
        "item_id": 24,
        "name": "Heather Cashmere Hoodie",
        "category": "top",
        "color": "heather gray",
        "warmth_level": "medium",
        "formality": "casual",
        "body_zone": "upper",
        "last_worn_date": "2024-12-21",
    },
    {
        "item_id": 25,
        "name": "Slate Tech Chinos",
        "category": "bottom",
        "color": "slate",
        "warmth_level": "light",
        "formality": "smart_casual",
        "body_zone": "lower",
        "last_worn_date": "2024-12-17",
    },
    {
        "item_id": 26,
        "name": "Forest Trail Runners",
        "category": "shoes",
        "color": "forest green",
        "warmth_level": "light",
        "formality": "casual",
        "body_zone": "shoe",
        "last_worn_date": "2024-12-16",
    },
    {
        "item_id": 27,
        "name": "Powder Blue Poplin Shirt",
        "category": "top",
        "color": "powder blue",
        "warmth_level": "light",
        "formality": "business",
        "body_zone": "upper",
        "last_worn_date": "2024-12-14",
    },
    {
        "item_id": 28,
        "name": "Espresso Wool Trousers",
        "category": "bottom",
        "color": "espresso",
        "warmth_level": "medium",
        "formality": "business",
        "body_zone": "lower",
        "last_worn_date": "2024-12-13",
    },
    {
        "item_id": 29,
        "name": "Burgundy Wingtip Oxfords",
        "category": "shoes",
        "color": "burgundy",
        "warmth_level": "medium",
        "formality": "business",
        "body_zone": "shoe",
        "last_worn_date": "2024-12-12",
    },
]


def reset_database() -> None:
    """Drop and recreate the wardrobe_items table."""
    if DB_PATH.exists():
        DB_PATH.unlink()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE wardrobe_items (
                item_id INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                color TEXT,
                warmth_level TEXT,
                formality TEXT,
                body_zone TEXT,
                last_worn_date TEXT
            )
            """
        )


def seed_items(items: Iterable[dict[str, str | int]]) -> None:
    """Populate the wardrobe_items table with demo content."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany(
            """
            INSERT INTO wardrobe_items (
                item_id,
                user_id,
                name,
                category,
                color,
                warmth_level,
                formality,
                body_zone,
                last_worn_date
            )
            VALUES (
                :item_id,
                :user_id,
                :name,
                :category,
                :color,
                :warmth_level,
                :formality,
                :body_zone,
                :last_worn_date
            )
            """,
            items,
        )


def main() -> None:
    """Recreate the demo wardrobe database from scratch."""
    reset_database()
    enriched_items = [{**item, "user_id": DEMO_USER_ID} for item in WARDROBE_ITEMS]
    seed_items(enriched_items)
    print(f"Seeded {len(WARDROBE_ITEMS)} wardrobe items into {DB_PATH}")


if __name__ == "__main__":
    main()
