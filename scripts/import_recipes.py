"""
Import script for Pākakṛti.
Imports recipes and pantry ingredients from data/pakakriti_high_protein_recipes.json into SQLite (data/recipes.db).
"""

import json
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "recipes.db"
JSON_PATH = DATA_DIR / "pakakriti_high_protein_recipes.json"

sys.path.insert(0, str(BASE_DIR))
from db import init_db


def run_import():
    if not JSON_PATH.exists():
        print(f"Error: JSON file not found at {JSON_PATH}")
        sys.exit(1)

    print(f"Initializing database schema at {DB_PATH}...")
    init_db()

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM ingredients")
    cursor.execute("DELETE FROM instructions")
    cursor.execute("DELETE FROM recipes")
    cursor.execute("DELETE FROM prepopulated_ingredients")

    try:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('recipes', 'ingredients', 'instructions', 'prepopulated_ingredients')")
    except sqlite3.OperationalError:
        pass

    pantry = data.get("pantry_ingredients", [])
    print(f"Importing {len(pantry)} pantry ingredients...")
    for item in pantry:
        names = item.get("names", {})
        nutr = item.get("nutrition_per_100g", {})
        ayur = item.get("ayurvedic_properties", {})

        cursor.execute("""
            INSERT INTO prepopulated_ingredients (
                name_en, name_hi, name_mr, category,
                calories_per_100g, protein, carbs, fat, fiber,
                zinc, iron, calcium, micronutrients,
                ayurvedic_significance, dosha_effect, taste_rasa, potency_virya
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            names.get("en", "").strip(),
            names.get("hi", "").strip(),
            names.get("mr", "").strip(),
            item.get("category", "General").strip(),
            nutr.get("calories", "").strip(),
            nutr.get("protein", "").strip(),
            nutr.get("carbs", "").strip(),
            nutr.get("fat", "").strip(),
            nutr.get("fiber", "").strip(),
            nutr.get("zinc", "").strip(),
            nutr.get("iron", "").strip(),
            nutr.get("calcium", "").strip(),
            item.get("active_compounds", "").strip(),
            ayur.get("significance", "").strip(),
            ayur.get("dosha_effect", "").strip(),
            ayur.get("rasa_taste", "").strip(),
            ayur.get("virya_potency", "").strip()
        ))

    recipes = data.get("recipes", [])
    print(f"Importing {len(recipes)} recipes...")
    for r in recipes:
        times = r.get("times", {})
        nutr = r.get("nutrition_per_serving", {})
        ayur = r.get("ayurvedic_profile", {})
        dosha = ayur.get("dosha_balance", "").strip()
        thera = ayur.get("therapeutic_note", "").strip()
        if dosha and thera:
            ayur_note = f"{dosha} | {thera}"
        else:
            ayur_note = dosha or thera

        cursor.execute("""
            INSERT INTO recipes (
                title, description, category, servings, yield_grams,
                prep_time, cook_time, total_time,
                calories, protein, carbs, fat, fiber,
                iron, zinc, ayurvedic_note, image_url, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r.get("title", "").strip(),
            r.get("description", "").strip(),
            r.get("category", "General").strip(),
            int(r.get("servings", 4)),
            int(r.get("yield_grams", 0) or 0),
            times.get("prep", "").strip(),
            times.get("cook", "").strip(),
            times.get("total", "").strip(),
            nutr.get("calories", "").strip(),
            nutr.get("protein", "").strip(),
            nutr.get("carbs", "").strip(),
            nutr.get("fat", "").strip(),
            nutr.get("fiber", "").strip(),
            nutr.get("iron", "").strip(),
            nutr.get("zinc", "").strip(),
            ayur_note,
            r.get("image_url", "/assets/placeholder_food.svg"),
            r.get("chef_notes", "").strip()
        ))
        recipe_id = cursor.lastrowid

        for idx, ing in enumerate(r.get("ingredients", []), 1):
            cursor.execute("""
                INSERT INTO ingredients (recipe_id, name, amount, unit, notes, order_index)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                recipe_id,
                ing.get("name", "").strip(),
                ing.get("amount", "").strip(),
                ing.get("unit", "").strip(),
                ing.get("notes", "").strip(),
                ing.get("order", idx)
            ))

        for idx, inst in enumerate(r.get("instructions", []), 1):
            cursor.execute("""
                INSERT INTO instructions (recipe_id, step_number, instruction_text)
                VALUES (?, ?, ?)
            """, (
                recipe_id,
                inst.get("step", idx),
                inst.get("text", "").strip()
            ))

    conn.commit()
    conn.close()
    print("✅ All recipes and pantry ingredients imported successfully!")


if __name__ == "__main__":
    run_import()
