#!/usr/bin/env python3
"""Import the Indian Food Composition Tables 2017 food list into the pantry.

The source dataset is distributed by nodef/ifct2017 under AGPL-3.0.  Values in
the source file are per 100 g edible portion; energy is supplied in kJ and the
minerals are supplied in g, so this importer converts those display values to
kcal and mg for the app's existing pantry UI.
"""

import argparse
import csv
import io
import sys
from pathlib import Path
from urllib.request import urlopen

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

import db


IFCT_SOURCE = "IFCT 2017"
IFCT_URL = "https://raw.githubusercontent.com/nodef/ifct2017/main/compositions/index.csv"


def display_number(value, unit, multiplier=1, precision=2):
    """Return a compact, unit-labelled nutrient value or an empty string."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    number *= multiplier
    return f"{number:.{precision}f}".rstrip("0").rstrip(".") + f" {unit}"


def load_rows(source_path):
    if source_path:
        with open(source_path, encoding="utf-8", newline="") as source_file:
            return list(csv.DictReader(source_file))

    with urlopen(IFCT_URL, timeout=30) as response:
        text = response.read().decode("utf-8")
    return list(csv.DictReader(io.StringIO(text)))


def import_rows(rows):
    conn = db.get_db_connection()
    cursor = conn.cursor()
    inserted = updated = 0

    for row in rows:
        code = row.get("code", "").strip()
        name = row.get("name", "").strip()
        if not code or not name:
            continue

        energy_kj = row.get("enerc", "")
        values = (
            name,
            row.get("grup", "General").strip() or "General",
            display_number(energy_kj, "kcal", multiplier=1 / 4.184, precision=0),
            display_number(row.get("protcnt"), "g"),
            display_number(row.get("choavldf"), "g"),
            display_number(row.get("fatce"), "g"),
            display_number(row.get("fibtg"), "g"),
            display_number(row.get("zn"), "mg", multiplier=1000),
            display_number(row.get("fe"), "mg", multiplier=1000),
            display_number(row.get("ca"), "mg", multiplier=1000),
            f"IFCT food code: {code}",
            IFCT_SOURCE,
            code,
            row.get("scie", "").strip(),
            row.get("lang", "").strip(),
            "per 100 g edible portion",
            float(energy_kj) if energy_kj else None,
        )
        cursor.execute(
            "SELECT id FROM prepopulated_ingredients WHERE source = ? AND source_code = ?",
            (IFCT_SOURCE, code),
        )
        exists = cursor.fetchone() is not None
        cursor.execute("""
            INSERT INTO prepopulated_ingredients (
                name_en, category, calories_per_100g, protein, carbs, fat, fiber,
                zinc, iron, calcium, micronutrients, source, source_code,
                scientific_name, regional_names, nutrition_basis, energy_kj
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source, source_code) WHERE source_code IS NOT NULL DO UPDATE SET
                name_en = excluded.name_en,
                category = excluded.category,
                calories_per_100g = excluded.calories_per_100g,
                protein = excluded.protein,
                carbs = excluded.carbs,
                fat = excluded.fat,
                fiber = excluded.fiber,
                zinc = excluded.zinc,
                iron = excluded.iron,
                calcium = excluded.calcium,
                micronutrients = excluded.micronutrients,
                scientific_name = excluded.scientific_name,
                regional_names = excluded.regional_names,
                nutrition_basis = excluded.nutrition_basis,
                energy_kj = excluded.energy_kj
        """, values)
        if exists:
            updated += 1
        else:
            inserted += 1

    conn.commit()
    conn.close()
    return inserted, updated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Existing IFCT compositions CSV; avoids downloading it.")
    args = parser.parse_args()
    if args.source and not args.source.is_file():
        parser.error(f"source file not found: {args.source}")

    db.init_db()
    rows = load_rows(args.source)
    inserted, updated = import_rows(rows)
    print(f"Imported IFCT 2017 pantry foods: {inserted} inserted, {updated} updated ({len(rows)} source rows).")


if __name__ == "__main__":
    main()
