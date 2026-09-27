"""
Database module for Rustic Recipe Card Maker.
Manages single-file SQLite database with pre-populated ingredients and starter recipes.
"""

import sqlite3
import os
import json
from pathlib import Path
from datetime import datetime

# Database file location
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "recipes.db"


def get_db_connection():
    """Returns a SQLite connection configured for WAL mode and dictionary rows."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initializes database schema, handles schema migrations, and populates starter data."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create tables
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT DEFAULT 'General',
        servings INTEGER DEFAULT 4,
        yield_grams INTEGER DEFAULT 0,
        prep_time TEXT DEFAULT '15 mins',
        cook_time TEXT DEFAULT '30 mins',
        total_time TEXT DEFAULT '45 mins',
        calories TEXT DEFAULT '',
        protein TEXT DEFAULT '',
        carbs TEXT DEFAULT '',
        fat TEXT DEFAULT '',
        fiber TEXT DEFAULT '',
        iron TEXT DEFAULT '',
        zinc TEXT DEFAULT '',
        ayurvedic_note TEXT DEFAULT '',
        image_url TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        amount TEXT,
        unit TEXT,
        notes TEXT,
        order_index INTEGER DEFAULT 0,
        FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS instructions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER NOT NULL,
        step_number INTEGER NOT NULL,
        instruction_text TEXT NOT NULL,
        FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS prepopulated_ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name_en TEXT NOT NULL,
        name_hi TEXT DEFAULT '',
        name_mr TEXT DEFAULT '',
        category TEXT NOT NULL,
        calories_per_100g TEXT DEFAULT '',
        protein TEXT DEFAULT '',
        carbs TEXT DEFAULT '',
        fat TEXT DEFAULT '',
        fiber TEXT DEFAULT '',
        zinc TEXT DEFAULT '',
        iron TEXT DEFAULT '',
        calcium TEXT DEFAULT '',
        micronutrients TEXT DEFAULT '',
        ayurvedic_significance TEXT DEFAULT '',
        dosha_effect TEXT DEFAULT '',
        taste_rasa TEXT DEFAULT '',
        potency_virya TEXT DEFAULT '',
        source TEXT DEFAULT 'custom',
        source_code TEXT,
        scientific_name TEXT DEFAULT '',
        regional_names TEXT DEFAULT '',
        nutrition_basis TEXT DEFAULT 'per 100 g',
        energy_kj REAL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()

    # Schema Migrations: Ensure all columns exist in recipes
    cursor.execute("PRAGMA table_info(recipes)")
    existing_recipe_cols = [row[1] for row in cursor.fetchall()]
    new_recipe_cols = {
        "calories": "TEXT DEFAULT ''",
        "protein": "TEXT DEFAULT ''",
        "carbs": "TEXT DEFAULT ''",
        "fat": "TEXT DEFAULT ''",
        "fiber": "TEXT DEFAULT ''",
        "iron": "TEXT DEFAULT ''",
        "zinc": "TEXT DEFAULT ''",
        "ayurvedic_note": "TEXT DEFAULT ''",
        "yield_grams": "INTEGER DEFAULT 0",
    }
    for col, definition in new_recipe_cols.items():
        if col not in existing_recipe_cols:
            cursor.execute(f"ALTER TABLE recipes ADD COLUMN {col} {definition}")
    conn.commit()

    # Preserve the identity and units of externally imported pantry records.
    # These nullable additions are safe for existing user-created ingredients.
    cursor.execute("PRAGMA table_info(prepopulated_ingredients)")
    existing_ing_cols = [row[1] for row in cursor.fetchall()]
    import_cols = {
        "source": "TEXT DEFAULT 'custom'",
        "source_code": "TEXT",
        "scientific_name": "TEXT DEFAULT ''",
        "regional_names": "TEXT DEFAULT ''",
        "nutrition_basis": "TEXT DEFAULT 'per 100 g'",
        "energy_kj": "REAL",
    }
    for col, definition in import_cols.items():
        if col not in existing_ing_cols:
            cursor.execute(f"ALTER TABLE prepopulated_ingredients ADD COLUMN {col} {definition}")
    conn.commit()

    # Schema Migrations: Check prepopulated_ingredients columns
    cursor.execute("PRAGMA table_info(prepopulated_ingredients)")
    existing_ing_cols = [row[1] for row in cursor.fetchall()]
    
    # If old table schema with single 'name' column exists, recreate table with rich schema
    if "name" in existing_ing_cols and "name_en" not in existing_ing_cols:
        cursor.execute("DROP TABLE IF EXISTS prepopulated_ingredients")
        cursor.execute("""
        CREATE TABLE prepopulated_ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_en TEXT NOT NULL,
            name_hi TEXT DEFAULT '',
            name_mr TEXT DEFAULT '',
            category TEXT NOT NULL,
            calories_per_100g TEXT DEFAULT '',
            protein TEXT DEFAULT '',
            carbs TEXT DEFAULT '',
            fat TEXT DEFAULT '',
            fiber TEXT DEFAULT '',
            zinc TEXT DEFAULT '',
            iron TEXT DEFAULT '',
            calcium TEXT DEFAULT '',
            micronutrients TEXT DEFAULT '',
            ayurvedic_significance TEXT DEFAULT '',
            dosha_effect TEXT DEFAULT '',
            taste_rasa TEXT DEFAULT '',
            potency_virya TEXT DEFAULT '',
            source TEXT DEFAULT 'custom',
            source_code TEXT,
            scientific_name TEXT DEFAULT '',
            regional_names TEXT DEFAULT '',
            nutrition_basis TEXT DEFAULT 'per 100 g',
            energy_kj REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
        seed_ingredients(conn)
    else:
        cursor.execute("SELECT COUNT(*) FROM prepopulated_ingredients")
        if cursor.fetchone()[0] == 0:
            seed_ingredients(conn)

    # Create this after a possible legacy-table rebuild, which drops indexes.
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_pantry_source_code
        ON prepopulated_ingredients(source, source_code)
        WHERE source_code IS NOT NULL
    """)
    conn.commit()

    # Check if starter recipes need seeding
    cursor.execute("SELECT COUNT(*) FROM recipes")
    if cursor.fetchone()[0] == 0:
        seed_recipes(conn)

    conn.close()


def seed_ingredients(conn):
    """Seeds rich kitchen and Ayurvedic ingredients with English, Hindi, Marathi names, nutrients, and Ayurvedic traits."""
    ingredients_data = [
        # Spices & Healing Herbs
        (
            "Turmeric", "हल्दी", "हळद", "Spices & Healing Herbs",
            "354 kcal", "7.8g", "65g", "9.9g", "21g",
            "4.3 mg", "41.4 mg", "182 mg",
            "Curcumin, Manganese, Vitamin C, Potassium, Vitamin B6",
            "Tridoshic in moderation. Powerful blood purifier (Rakta Shodhaka), anti-inflammatory, kindles Agni without aggravating Pitta, enhances Ojas and skin luster (Varnya).",
            "Vata ↓ | Pitta = | Kapha ↓", "Tikta (Bitter), Katu (Pungent)", "Ushna (Heating)"
        ),
        (
            "Cumin Seeds (Jeera)", "जीरा", "जिरे", "Spices & Healing Herbs",
            "375 kcal", "18g", "44g", "22g", "10.5g",
            "4.8 mg", "66.4 mg", "931 mg",
            "Thymol, Cuminaldehyde, Magnesium, Phosphorus",
            "Supreme Deepana (kindles digestive fire) and Pachana (clears toxins/Ama). Relieves bloating, colic, and abdominal cramps while calming Vata and Kapha.",
            "Vata ↓ | Pitta = | Kapha ↓", "Katu (Pungent), Tikta (Bitter)", "Ushna (Heating)"
        ),
        (
            "Fresh Ginger Root", "अदरक / ताज़ा अदरक", "आले", "Fresh Herbs & Aromatics",
            "80 kcal", "1.8g", "18g", "0.8g", "2.0g",
            "0.34 mg", "0.6 mg", "16 mg",
            "Gingerols, Shogaols, Vitamin C, Potassium",
            "Known as Vishwabhesaja (Universal Medicine). Ignites Agni, stimulates salivary secretions, alleviates nausea, joint stiffness, and respiratory congestion.",
            "Vata ↓ | Pitta = | Kapha ↓", "Katu (Pungent), Madhura (Sweet)", "Ushna (Heating)"
        ),
        (
            "Dry Ginger Powder (Sunthi)", "सोंठ", "सुंठ", "Spices & Healing Herbs",
            "335 kcal", "9g", "72g", "4.2g", "14g",
            "3.6 mg", "19.8 mg", "114 mg",
            "Zingerone, Shogaols, Essential Oils",
            "Less heating to Pitta than fresh ginger, Grahi (absorptive/bowel regulator), powerful Vata-Kapha pacifier, excellent for sluggish digestion and joint health.",
            "Vata ↓ | Pitta = | Kapha ↓", "Katu (Pungent), Madhura post-digestive", "Snigdha, Ushna (Heating)"
        ),
        (
            "Fenugreek Seeds (Methi)", "मेथी दाना", "मेथी दाणे", "Spices & Healing Herbs",
            "323 kcal", "23g", "58g", "6.4g", "25g",
            "2.5 mg", "33.5 mg", "176 mg",
            "Trigonelline, Diosgenin, Saponins, 4-Hydroxyisoleucine",
            "Potent Vata and Kapha pacifier. Promotes healthy blood sugar, strengthens bone marrow and reproductive tissue (Shukra), relieves lower back aching and stiffness.",
            "Vata ↓ | Pitta ↑ | Kapha ↓", "Tikta (Bitter), Kashaya (Astringent)", "Ushna (Heating)"
        ),
        (
            "Cardamom (Green Elaichi)", "छोटी इलायची", "हिरवी वेलची", "Spices & Healing Herbs",
            "311 kcal", "11g", "68g", "6.7g", "28g",
            "7.5 mg", "14.0 mg", "383 mg",
            "Terpinyl acetate, Cineole, Flavonoids",
            "Tridoshic, supreme aromatic harmonizer. Sheeta (cooling post-digestion), Hridya (nourishes the heart & mind), clears excess Kapha and stomach acidity.",
            "Vata ↓ | Pitta ↓ | Kapha ↓", "Madhura (Sweet), Katu (Pungent)", "Sheeta (Cooling)"
        ),
        (
            "Pure Desi Cow Ghee", "देसी गाय का घी", "गायीचे साजूक तूप", "Dairy & Ghee",
            "884 kcal", "0.3g", "0g", "99.5g", "0g",
            "0.2 mg", "0.2 mg", "12 mg",
            "Butyric acid, Conjugated Linoleic Acid (CLA), Vitamin A, D, E, K",
            "The foremost Rasayana lipid in Ayurveda. Balances Vata and Pitta, boosts Ojas (vital immunity), carries herbs deep into Dhatus (Yogavahi), lubricates joints and intellect.",
            "Vata ↓ | Pitta ↓ | Kapha =/↑", "Madhura (Sweet)", "Sheeta (Cooling)"
        ),
        (
            "Garlic (Lahsun)", "लहसुन", "लसूण", "Fresh Herbs & Aromatics",
            "149 kcal", "6.4g", "33g", "0.5g", "2.1g",
            "1.2 mg", "1.7 mg", "181 mg",
            "Allicin, Ajoene, Selenium, Vitamin B6",
            "Known as Rasona (possessing 5 tastes except sour). Powerful Vata destroyer, strengthens heart and blood vessels, dispels intestinal worms and deep-seated chills.",
            "Vata ↓ | Pitta ↑ | Kapha ↓", "Katu, Madhura, Tikta, Lavana, Kashaya", "Ushna (Heating)"
        ),
        (
            "Black Peppercorns (Kali Mirch)", "काली मिर्च", "काळी मिरी", "Spices & Healing Herbs",
            "255 kcal", "10.4g", "64g", "3.3g", "25.3g",
            "1.3 mg", "9.7 mg", "443 mg",
            "Piperine, Caryophyllene, Chromium",
            "Pramathi (scrapes and opens micro-channels/Srotas), burns Ama, boosts bioavailability of curcumin and minerals, eliminates Kapha congestion.",
            "Vata ↓ | Pitta ↑ | Kapha ↓", "Katu (Pungent)", "Ushna (Heating)"
        ),
        (
            "Cloves (Laung)", "लौंग", "लवंग", "Spices & Healing Herbs",
            "274 kcal", "6.0g", "66g", "13.0g", "34g",
            "1.1 mg", "11.8 mg", "632 mg",
            "Eugenol, Tannins, Manganese, Gallic Acid",
            "Deepana and Pachana. Relieves toothache, upper respiratory phlegm, improves eyesight (Chakshushya), pacifies Kapha and Pitta when used judiciously.",
            "Vata ↓ | Pitta = | Kapha ↓", "Katu (Pungent), Tikta (Bitter)", "Sheeta post-digestive"
        ),
        (
            "Cinnamon (Dalchini)", "दालचीनी", "दालचिनी", "Spices & Healing Herbs",
            "247 kcal", "4.0g", "81g", "1.2g", "53g",
            "1.8 mg", "8.3 mg", "1002 mg",
            "Cinnamaldehyde, Proanthocyanidins, Polyphenols",
            "Kindles digestive and metabolic fire, balances insulin response, pacifies Vata and Kapha, warms the extremities and lungs.",
            "Vata ↓ | Pitta ↑ | Kapha ↓", "Madhura, Tikta, Katu", "Ushna (Heating)"
        ),
        (
            "Coriander Seeds (Dhaniya)", "धनिया बीज", "धने", "Spices & Healing Herbs",
            "298 kcal", "12g", "55g", "18g", "42g",
            "4.7 mg", "16.3 mg", "709 mg",
            "Linalool, Pinene, Vitamin C, Beta-Carotene",
            "Tridoshic, specially Pitta-soothing. Sheeta virya, clears urinary burning (Mutrakrichra), enhances digestion without heat, harmonizes digestive secretions.",
            "Vata ↓ | Pitta ↓ | Kapha ↓", "Kashaya (Astringent), Tikta (Bitter), Madhura", "Sheeta (Cooling)"
        ),
        (
            "Mustard Seeds (Rai / Sarson)", "राई / सरसों", "मोहरी", "Spices & Healing Herbs",
            "508 kcal", "26g", "28g", "36g", "12g",
            "6.1 mg", "9.2 mg", "266 mg",
            "Glucosinolates, Sinigrin, Omega-3, Selenium",
            "Ushna virya, powerfully dispels cold Kapha and Vata stagnation, stimulates bile and peripheral blood circulation.",
            "Vata ↓ | Pitta ↑ | Kapha ↓", "Katu (Pungent), Tikta (Bitter)", "Ushna (Heating)"
        ),
        (
            "Fennel Seeds (Saunf)", "सौंफ", "बडीशेप", "Spices & Healing Herbs",
            "345 kcal", "16g", "52g", "15g", "40g",
            "3.7 mg", "18.5 mg", "1196 mg",
            "Anethole, Fenchone, Flavonoids, Magnesium",
            "Tridoshic, supreme cooling carminative. Balances Pitta and Vata, relaxes stomach spasms, improves mental focus and visual acuity.",
            "Vata ↓ | Pitta ↓ | Kapha ↓", "Madhura (Sweet), Tikta (Bitter)", "Sheeta (Cooling)"
        ),
        (
            "Asafoetida (Hing)", "हींग", "हिंग", "Spices & Healing Herbs",
            "297 kcal", "4.0g", "68g", "1.1g", "4.1g",
            "0.5 mg", "39.4 mg", "690 mg",
            "Ferulic acid, Umbelliferone, Sulfur compounds",
            "Unrivaled carminative for Vata in the lower abdomen (Apana Vayu). Relieves gas, heavy pulse fermentation, and intestinal cramps instantly.",
            "Vata ↓ | Pitta ↑ | Kapha ↓", "Katu (Pungent)", "Ushna (Heating)"
        ),
        (
            "Ashwagandha Root Powder", "अश्वगंधा", "अश्वगंधा", "Healing Botanicals & Tonics",
            "277 kcal", "3.7g", "50g", "0.3g", "36g",
            "2.3 mg", "18.2 mg", "170 mg",
            "Withanolides, Alkaloids, Iron, Saponins",
            "Supreme adaptogenic Rasayana. Balances Vata and Kapha, builds stamina (Bala), regenerates nerve and reproductive tissues, calms racing thoughts.",
            "Vata ↓ | Pitta = | Kapha ↓", "Tikta (Bitter), Kashaya (Astringent), Madhura", "Ushna (Heating)"
        ),
        (
            "Holy Basil / Tulsi", "तुलसी", "तुळस", "Fresh Herbs & Aromatics",
            "22 kcal", "3.1g", "2.6g", "0.6g", "1.6g",
            "0.8 mg", "3.2 mg", "177 mg",
            "Eugenol, Ursolic acid, Rosmarinic acid, Zinc, Iron",
            "Sacred herb of longevity. Expands Prana (vital life force), purifies blood and respiratory channels, elevates Sattva (mental clarity and peace).",
            "Vata ↓ | Pitta = | Kapha ↓", "Katu (Pungent), Tikta (Bitter)", "Ushna (Heating)"
        ),
        (
            "Amla (Indian Gooseberry)", "आंवला", "आवळा", "Produce & Superfoods",
            "44 kcal", "0.9g", "10g", "0.6g", "4.3g",
            "0.12 mg", "1.2 mg", "25 mg",
            "Natural Bio-available Vitamin C, Gallic Acid, Ellagic Acid, Tannins",
            "Premier Rasayana of Charaka Samhita. Possesses 5 of the 6 tastes (all except salty). Deeply balances Pitta, strengthens eyesight, hair, and immunity without increasing cold.",
            "Vata ↓ | Pitta ↓ | Kapha ↓", "Amla (Sour), Kashaya, Madhura, Tikta, Katu", "Sheeta (Cooling)"
        ),
        (
            "Kashmiri Saffron (Kesar)", "केसर", "केशर", "Spices & Healing Herbs",
            "310 kcal", "11.4g", "65g", "5.8g", "3.9g",
            "1.1 mg", "11.1 mg", "111 mg",
            "Crocin, Safranal, Picrocrocin, Potassium",
            "Tridoshic golden spice. Rejuvenates Dhatus, uplifts mood and neurochemistry, enhances skin complexion (Varnya), strengthens heart and reproductive tissue.",
            "Vata ↓ | Pitta = | Kapha ↓", "Tikta (Bitter), Katu (Pungent)", "Ushna (Heating)"
        ),
        (
            "Sesame Seeds (Til)", "सफेद / काला तिल", "पांढरे / काळे तीळ", "Nuts & Seeds",
            "573 kcal", "18g", "23g", "50g", "12g",
            "7.8 mg", "14.6 mg", "975 mg",
            "Sesamin, Sesamol, Calcium, Iron, Zinc, Copper",
            "Foremost oilseed for calming Vata. Deeply nourishes Asthi (bones), teeth, joints, and skin. Imparts deep warmth and structural strength.",
            "Vata ↓ | Pitta ↑ | Kapha ↑", "Madhura, Tikta, Kashaya, Katu", "Ushna (Heating)"
        ),
        (
            "Moong Dal (Yellow / Green)", "मूँग दाल", "मूग डाळ", "Lentils & Pulses",
            "347 kcal", "24g", "60g", "1.2g", "16g",
            "2.7 mg", "6.7 mg", "132 mg",
            "Folate, Iron, Magnesium, Potassium, Plant Protein",
            "The lightest and most sattvic pulse in Ayurveda. Tridoshic, easily assimilated during illness or convalescence, rebuilds tissues without gas or bloating.",
            "Vata ↓ | Pitta ↓ | Kapha ↓", "Madhura (Sweet), Kashaya (Astringent)", "Sheeta (Cooling)"
        ),
        (
            "Black Gram (Urad Dal)", "उड़द दाल", "उडीद डाळ", "Lentils & Pulses",
            "341 kcal", "25g", "59g", "1.6g", "18g",
            "3.3 mg", "7.6 mg", "138 mg",
            "Complex Protein, Iron, Zinc, Phosphorus",
            "Heavy and deeply nourishing (Guru & Snigdha). Powerful Vata pacifier, builds muscle mass (Mamsa), strengthens lactation and reproductive vitality.",
            "Vata ↓ | Pitta ↑ | Kapha ↑", "Madhura (Sweet)", "Ushna (Heating)"
        ),
        (
            "Chickpeas / Bengal Gram (Chana)", "काबुली चना / काला चना", "हरभरा / छोले", "Lentils & Pulses",
            "364 kcal", "19g", "61g", "6.0g", "17g",
            "3.4 mg", "6.2 mg", "105 mg",
            "Resistant starch, Plant Protein, Iron, Zinc",
            "Balances Pitta and Kapha. Provides sustained endurance and satiety, astringent tone to intestines.",
            "Vata ↑ | Pitta ↓ | Kapha ↓", "Kashaya (Astringent), Madhura (Sweet)", "Sheeta (Cooling)"
        ),
        (
            "Almonds (Badam)", "बादाम", "बदाम", "Nuts & Seeds",
            "579 kcal", "21g", "22g", "50g", "12.5g",
            "3.1 mg", "3.7 mg", "269 mg",
            "Vitamin E, Magnesium, Riboflavin, L-Carnitine",
            "Medhya Rasayana (brain and nervous system tonic). Balances Vata and Pitta when soaked and peeled. Builds physical strength and vital Ojas.",
            "Vata ↓ | Pitta ↓ | Kapha ↑", "Madhura (Sweet)", "Ushna / Snigdha"
        ),
        (
            "Walnuts (Akhrot)", "अखरोट", "अक्रोड", "Nuts & Seeds",
            "654 kcal", "15g", "14g", "65g", "6.7g",
            "3.1 mg", "2.9 mg", "98 mg",
            "Alpha-Linolenic Acid (ALA Omega-3), Polyphenols",
            "Nourishes Majja Dhatu (bone marrow and neurological tissue). Dispels mental fatigue, balances Vata, lubricates dry tissues.",
            "Vata ↓ | Pitta = | Kapha ↑", "Madhura (Sweet), Kashaya", "Ushna (Heating)"
        ),
        (
            "Fresh Spinach (Palak)", "पालक", "पालक", "Produce & Vegetables",
            "23 kcal", "2.9g", "3.6g", "0.4g", "2.2g",
            "0.5 mg", "2.7 mg", "99 mg",
            "Chlorophyll, Lutein, Iron, Folic Acid, Vitamin K",
            "Rakta-vardhaka (nourishes blood plasma). Cooling and restorative, pacifies Pitta and Kapha, gentle natural laxative.",
            "Vata =/↑ | Pitta ↓ | Kapha ↓", "Tikta (Bitter), Kashaya (Astringent)", "Sheeta (Cooling)"
        ),
        (
            "Organic Jaggery (Gur)", "गुड़", "गूळ", "Sweeteners & Sugars",
            "383 kcal", "0.4g", "98g", "0.1g", "0g",
            "0.4 mg", "11.4 mg", "80 mg",
            "Unrefined sucrose, Iron, Potassium, Magnesium",
            "Aged jaggery (Purana Guda) is light, clears the respiratory tracts, purifies blood, balances Vata, and kindles digestive Agni compared to refined sugar.",
            "Vata ↓ | Pitta = | Kapha ↑", "Madhura (Sweet), Kshara", "Ushna (Heating)"
        ),
        (
            "Rock Salt (Saindhava Lavana / Pink Salt)", "सेंधा नमक", "शेंदेलोण / सैंधव मीठ", "Spices & Healing Herbs",
            "0 kcal", "0g", "0g", "0g", "0g",
            "0.3 mg", "2.1 mg", "40 mg",
            "84+ Trace minerals, Natural Electrolytes",
            "The finest salt in Ayurveda. Hridya (good for the heart), Chakshushya (cooling to eyes), does not cause fluid retention or aggravate Pitta like sea salt.",
            "Vata ↓ | Pitta ↓ | Kapha ↓", "Lavana (Salty), Madhura post-digestive", "Sheeta (Cooling)"
        ),
        (
            "Nutmeg (Jaiphal)", "जायफल", "जायफळ", "Spices & Healing Herbs",
            "525 kcal", "5.8g", "49g", "36g", "21g",
            "2.2 mg", "3.0 mg", "184 mg",
            "Myristicin, Elemicin, Zinc, Magnesium",
            "Nidrajanana (natural sleep promoter) and Dipana. Calms an overactive nervous system, stops diarrhea, pacifies Vata and Kapha in pinch doses.",
            "Vata ↓ | Pitta = | Kapha ↓", "Katu (Pungent), Tikta (Bitter), Kashaya", "Ushna (Heating)"
        ),
        (
            "Indian Bay Leaf (Tejpatta)", "तेजपत्ता", "तमालपत्र", "Fresh Herbs & Aromatics",
            "313 kcal", "7.6g", "75g", "8.4g", "26g",
            "3.7 mg", "43.0 mg", "834 mg",
            "Eugenol, Tannins, Flavonoids, Iron",
            "Aromatic warming leaf that stimulates insulin sensitivity, dispels gas, and balances Vata and Kapha without excessive heat.",
            "Vata ↓ | Pitta = | Kapha ↓", "Katu (Pungent), Madhura", "Ushna (Heating)"
        ),
        (
            "Fresh Coconut (Nariyal)", "नारियल", "खोबरे / नारळ", "Produce & Vegetables",
            "354 kcal", "3.3g", "15g", "33g", "9.0g",
            "1.1 mg", "2.4 mg", "14 mg",
            "Medium Chain Triglycerides (Lauric acid), Potassium",
            "Deeply cooling and rejuvenating (Brimhana). Calms excess Pitta and Vata, nourishes hair, liver, and restores electrolyte harmony.",
            "Vata ↓ | Pitta ↓ | Kapha ↑", "Madhura (Sweet)", "Sheeta (Cooling)"
        ),
        (
            "Star Anise (Chakra Phool)", "चक्र फूल", "चक्रफूल", "Spices & Healing Herbs",
            "337 kcal", "18g", "50g", "16g", "14.6g",
            "2.1 mg", "37.0 mg", "646 mg",
            "Shikimic acid, Anethole, Iron",
            "Kapha-Vata dispelling spice. Supports respiratory clear breathing, relieves gastrointestinal stagnation and colic.",
            "Vata ↓ | Pitta = | Kapha ↓", "Madhura (Sweet), Katu (Pungent)", "Ushna (Heating)"
        ),
        (
            "Fresh Mint (Pudina)", "पुदीना", "पुदिना", "Fresh Herbs & Aromatics",
            "44 kcal", "3.8g", "8.4g", "0.9g", "6.8g",
            "1.1 mg", "5.1 mg", "243 mg",
            "Menthol, Menthone, Rosmarinic acid",
            "Cooling aromatic carminative. Balances Pitta and Kapha, cleanses palate, settles nausea and summer stomach heat.",
            "Vata = | Pitta ↓ | Kapha ↓", "Katu (Pungent), Tikta (Bitter)", "Sheeta (Cooling)"
        ),
        (
            "Curry Leaves (Kadi Patta)", "कढ़ी पत्ता", "कढीपत्ता", "Fresh Herbs & Aromatics",
            "108 kcal", "6.1g", "18g", "1.0g", "6.4g",
            "0.2 mg", "8.7 mg", "830 mg",
            "Mahanimbine, Beta-Carotene, Calcium, Iron",
            "Pitta-Kapha soothing herb. Protects liver enzymes (Yakrit-rakshaka), stimulates digestive enzymes, prevents premature hair graying.",
            "Vata = | Pitta ↓ | Kapha ↓", "Tikta (Bitter), Kashaya (Astringent)", "Sheeta (Cooling)"
        ),
        (
            "Carom Seeds (Ajwain)", "अजवाइन", "ओवा", "Spices & Healing Herbs",
            "305 kcal", "16g", "43g", "25g", "39g",
            "5.0 mg", "13.7 mg", "1525 mg",
            "Thymol, Terpinene, Pinene",
            "The quickest home remedy for acute Vata gas and abdominal distension. Potent Deepana, clears mucus from chest and gut.",
            "Vata ↓ | Pitta ↑ | Kapha ↓", "Katu (Pungent), Tikta (Bitter)", "Ushna (Heating)"
        ),
        (
            "Kokum (Amsul)", "कोकम", "आमसूल / कोकम", "Produce & Vegetables",
            "60 kcal", "1.2g", "14g", "0.2g", "4.1g",
            "0.2 mg", "2.1 mg", "45 mg",
            "Garcinol, Hydroxycitric Acid (HCA), Anthocyanins",
            "Celebrated Coastal Western Ghats cooling fruit. Supreme Pitta reducer, relieves acidity, heat exhaustion, and sun allergies.",
            "Vata = | Pitta ↓ | Kapha ↓", "Amla (Sour), Kashaya (Astringent)", "Sheeta (Cooling)"
        ),
        (
            "Whole Wheat Flour (Atta)", "गेहूं का आटा", "गव्हाचे पीठ", "Baking & Grains",
            "340 kcal", "13g", "72g", "2.5g", "10.7g",
            "2.9 mg", "3.9 mg", "34 mg",
            "B-Complex Vitamins, Phosphorus, Zinc",
            "Ground staple grain. Balances Vata and Pitta, builds body mass (Brimhana), provides sustained muscular strength.",
            "Vata ↓ | Pitta ↓ | Kapha ↑", "Madhura (Sweet)", "Sheeta (Cooling)"
        ),
        (
            "Basmati Rice (Chawal)", "बासमती चावल", "बासमती तांदूळ", "Baking & Grains",
            "356 kcal", "7.1g", "78g", "0.7g", "1.3g",
            "1.1 mg", "1.2 mg", "10 mg",
            "Easily digestible carbohydrates, Low Amylose",
            "Tridoshic grain praised in Ayurveda as Rakthashali equivalent. Light to digest, cooling, nourishing to all bodily tissues.",
            "Vata ↓ | Pitta ↓ | Kapha =", "Madhura (Sweet)", "Sheeta (Cooling)"
        ),
        (
            "Whole Milk (Cow Doodh)", "गाय का दूध", "गायीचे दूध", "Dairy & Ghee",
            "62 kcal", "3.2g", "4.8g", "3.6g", "0g",
            "0.4 mg", "0.1 mg", "120 mg",
            "Casein, Whey, Calcium, Vitamin D, Vitamin B12",
            "Supreme natural Rasayana for Vata and Pitta. Imparts Ojas, strengthens bone density, calms mind when boiled with cardamom and turmeric.",
            "Vata ↓ | Pitta ↓ | Kapha ↑", "Madhura (Sweet)", "Sheeta (Cooling)"
        ),
        (
            "Fresh Curd / Yogurt (Dahi)", "दही", "दही", "Dairy & Ghee",
            "61 kcal", "3.5g", "4.7g", "3.3g", "0g",
            "0.6 mg", "0.1 mg", "121 mg",
            "Probiotic Lactobacillus cultures, Bioavailable Calcium",
            "Ushna virya and Guru (heavy). Kindles digestive Agni, builds strength, best consumed during daytime with cumin or rock salt; avoid at night.",
            "Vata ↓ | Pitta ↑ | Kapha ↑", "Amla (Sour), Madhura (Sweet)", "Ushna (Heating)"
        ),
        (
            "Indian Cottage Cheese (Paneer)", "पनीर", "पनीर", "Dairy & Ghee",
            "265 kcal", "18.3g", "1.2g", "20.8g", "0g",
            "2.7 mg", "2.1 mg", "208 mg",
            "Complete Milk Protein, Calcium, Phosphorus",
            "Rich tissue builder (Mamsa-vardhaka). Balances Vata, provides substantial strength and satiety for vegetarians.",
            "Vata ↓ | Pitta ↓ | Kapha ↑", "Madhura (Sweet)", "Sheeta (Cooling)"
        ),
        (
            "Raw Honey (Madhu)", "शुद्ध शहद", "शुद्ध मध", "Sweeteners & Sugars",
            "304 kcal", "0.3g", "82g", "0g", "0.2g",
            "0.2 mg", "0.4 mg", "6 mg",
            "Flavonoids, Bee Pollen enzymes, Fructose",
            "Lekhana (scrapes excess fat and Kapha) and Yogavahi (carrier herb enhancer). Never heat above body temperature as it generates toxic Ama.",
            "Vata = | Pitta = | Kapha ↓", "Madhura (Sweet), Kashaya (Astringent)", "Ushna / Ruksha"
        ),
        (
            "All-Purpose Flour (Maida)", "मैदा", "मैदा", "Baking & Grains",
            "364 kcal", "10g", "76g", "1.0g", "2.7g",
            "0.7 mg", "1.2 mg", "15 mg",
            "Endosperm starch, Gluten",
            "Fine wheat flour suited for delicate pastries, cookies, and layered breads.",
            "Vata ↓ | Pitta = | Kapha ↑", "Madhura (Sweet)", "Sheeta (Cooling)"
        ),
        (
            "Unsalted Butter (Makkhan)", "सफ़ेद मक्खन", "लोणी", "Dairy & Ghee",
            "717 kcal", "0.9g", "0.1g", "81g", "0g",
            "0.1 mg", "0.1 mg", "24 mg",
            "Short-chain fatty acids, Vitamin A",
            "Freshly churned butter (Navanita) is cooling, kindles appetite, and nourishes the heart without clogging channels like old processed fats.",
            "Vata ↓ | Pitta ↓ | Kapha =", "Madhura (Sweet), Kashaya", "Sheeta (Cooling)"
        ),
        (
            "Extra Virgin Olive Oil", "जैतून का तेल", "ऑलिव्ह तेल", "Pantry & Oils",
            "884 kcal", "0g", "0g", "100g", "0g",
            "0.1 mg", "0.6 mg", "1 mg",
            "Monounsaturated Oleic Acid, Polyphenols, Vitamin E",
            "Heart-healthy antioxidant oil. Calms dry Vata skin and tissues.",
            "Vata ↓ | Pitta = | Kapha ↑", "Madhura, Tikta", "Snigdha, Ushna"
        ),
        (
            "Fresh Rosemary", "रोज़मेरी / गुलमेंहदी", "रोझमेरी", "Fresh Herbs & Aromatics",
            "131 kcal", "3.3g", "21g", "5.9g", "14g",
            "0.9 mg", "6.6 mg", "317 mg",
            "Rosmarinic acid, Carnosol, Camphor",
            "Warming aromatic European herb. Stimulates cerebral blood flow and mental clarity, dispels cold Kapha.",
            "Vata ↓ | Pitta ↑ | Kapha ↓", "Katu, Tikta", "Ushna (Heating)"
        ),
        (
            "Fresh Lemons", "नींबू", "लिंबू", "Produce & Vegetables",
            "29 kcal", "1.1g", "9.3g", "0.3g", "2.8g",
            "0.1 mg", "0.6 mg", "26 mg",
            "Citric acid, Ascorbic acid, Limonene, Bioflavonoids",
            "Stimulates salivary and stomach digestive juices. Enhances iron absorption from greens, clears heavy food aftertaste.",
            "Vata ↓ | Pitta = | Kapha ↓", "Amla (Sour)", "Sheeta (Cooling)"
        )
    ]

    cursor = conn.cursor()
    cursor.executemany("""
        INSERT INTO prepopulated_ingredients (
            name_en, name_hi, name_mr, category,
            calories_per_100g, protein, carbs, fat, fiber,
            zinc, iron, calcium, micronutrients,
            ayurvedic_significance, dosha_effect, taste_rasa, potency_virya
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ingredients_data)
    conn.commit()


def seed_recipes(conn):
    """Seeds starter recipes with rich nutritional & Ayurvedic profiles."""
    starter_recipes = [
        {
            "title": "Golden Turmeric Milk (Haldi Doodh)",
            "description": "Authentic Ayurvedic healing elixir crafted with spiced cow milk, golden turmeric, green cardamom, black pepper, and pure desi ghee.",
            "category": "Healing Elixirs & Teas",
            "servings": 2,
            "prep_time": "5 mins",
            "cook_time": "10 mins",
            "total_time": "15 mins",
            "calories": "145 kcal",
            "protein": "5g",
            "carbs": "12g",
            "fat": "8g",
            "fiber": "1g",
            "iron": "3.5 mg",
            "zinc": "1.2 mg",
            "ayurvedic_note": "Tridoshic | Boosts Ojas, immunity, and restful deep sleep.",
            "image_url": "/assets/placeholder_food.svg",
            "notes": "Always add a pinch of freshly crushed black pepper to activate curcumin absorption by up to 2000%.",
            "ingredients": [
                ("Whole Milk (Cow Doodh)", "2", "cups", "boiled fresh"),
                ("Turmeric (हल्दी / हळद)", "1/2", "tsp", "pure aromatic powder"),
                ("Black Peppercorns (Kali Mirch)", "1/4", "tsp", "freshly crushed"),
                ("Cardamom (Green Elaichi)", "2", "pods", "lightly crushed"),
                ("Dry Ginger Powder (Sunthi)", "1/4", "tsp", "optional for extra warmth"),
                ("Pure Desi Cow Ghee", "1/2", "tsp", "stirred in hot"),
                ("Organic Jaggery (Gur)", "1", "tsp", "sweetener to taste (stirred after cooling slightly)")
            ],
            "instructions": [
                "Pour milk into a heavy-bottomed brass or stainless steel saucepan over medium heat.",
                "Whisk in turmeric powder, crushed green cardamom pods, and dry ginger powder.",
                "Bring the golden milk to a gentle simmer for 5 to 7 minutes to let the botanical aromas infuse.",
                "Turn off heat, stir in a dollop of pure desi cow ghee and a pinch of black pepper.",
                "Strain into warm rustic mugs. Sweeten with jaggery or raw honey once lukewarm and sip mindfully."
            ]
        },
        {
            "title": "Grandma's Rustic Chocolate Chip Cookies",
            "description": "Crisp, golden caramelized edges with chewy, molten chocolate pockets, browned butter, and flaky sea salt.",
            "category": "Baking & Desserts",
            "servings": 24,
            "prep_time": "20 mins",
            "cook_time": "12 mins",
            "total_time": "32 mins",
            "calories": "210 kcal",
            "protein": "3g",
            "carbs": "28g",
            "fat": "11g",
            "fiber": "1g",
            "iron": "1.4 mg",
            "zinc": "0.6 mg",
            "ayurvedic_note": "Indulgent sweet | Satisfies Vata, best enjoyed fresh.",
            "image_url": "/assets/sample_cookies.svg",
            "notes": "Chill the dough for at least 2 hours or overnight for the deepest toffee-like flavor.",
            "ingredients": [
                ("All-Purpose Flour (Maida)", "2 1/4", "cups", "spooned and leveled"),
                ("Unsalted Butter (Makkhan)", "1", "cup", "browned and slightly cooled"),
                ("Brown Sugar", "1", "cup", "packed dark brown"),
                ("Granulated Sugar", "1/2", "cup", ""),
                ("Large Eggs", "2", "", "room temperature"),
                ("Pure Vanilla Extract", "2", "tsp", "high quality"),
                ("Baking Soda", "1", "tsp", ""),
                ("Rock Salt (Saindhava Lavana)", "1/2", "tsp", ""),
                ("Dark Chocolate Chips", "1 1/2", "cups", "roughly chopped discs or chips"),
                ("Flaky Sea Salt", "1", "tsp", "for sprinkling on top")
            ],
            "instructions": [
                "Brown the butter in a saucepan over medium heat until fragrant and nutty with golden flecks (~5 mins). Cool 10 minutes.",
                "In a large mixing bowl, whisk together the browned butter, brown sugar, and granulated sugar until well combined.",
                "Whisk in the eggs one at a time, followed by pure vanilla extract, beating vigorously until pale and thickened.",
                "Fold in flour, baking soda, and rock salt with a wooden spoon just until dry streaks disappear.",
                "Gently fold in dark chocolate chunks. Chill dough in refrigerator for at least 2 hours.",
                "Preheat oven to 375°F (190°C). Scoop 2-tablespoon dough mounds onto a parchment-lined baking sheet, 2 inches apart.",
                "Bake for 10-12 minutes until edges are golden brown. Immediately sprinkle with flaky sea salt while hot."
            ]
        },
        {
            "title": "Artisan Rosemary & Sea Salt Focaccia",
            "description": "Golden olive oil crusted bread with deep pillowy pockets, fresh aromatic rosemary, and crunchy sea salt flakes.",
            "category": "Breads & Baking",
            "servings": 8,
            "prep_time": "25 mins",
            "cook_time": "25 mins",
            "total_time": "3 hrs",
            "calories": "260 kcal",
            "protein": "6g",
            "carbs": "38g",
            "fat": "9g",
            "fiber": "2g",
            "iron": "2.1 mg",
            "zinc": "0.9 mg",
            "ayurvedic_note": "Warm & Grounding | Balances Vata with rich olive oil.",
            "image_url": "/assets/sample_focaccia.svg",
            "notes": "Do not skimp on the olive oil in the pan—it is what gives the focaccia its delightfully crispy, golden crust.",
            "ingredients": [
                ("Bread Flour", "4", "cups", "high protein"),
                ("Instant Yeast", "2", "tsp", ""),
                ("Warm Water", "1 3/4", "cups", "about 105°F"),
                ("Honey", "1", "tbsp", "or maple syrup"),
                ("Extra Virgin Olive Oil", "1/3", "cup", "divided"),
                ("Rock Salt (Saindhava Lavana)", "2", "tsp", "fine"),
                ("Fresh Rosemary", "3", "tbsp", "roughly chopped leaves"),
                ("Flaky Sea Salt", "1", "tbsp", "for topping")
            ],
            "instructions": [
                "In a large bowl, whisk together warm water, honey, and instant yeast. Let stand 5 minutes until frothy.",
                "Add bread flour and fine salt. Stir with a wooden spoon until a wet, sticky dough forms. Drizzle with 2 tbsp olive oil.",
                "Perform 4 stretch-and-folds every 30 minutes over 2 hours until dough is elastic and bubbly.",
                "Pour 3 tbsp olive oil into a 9x13 inch baking pan. Transfer dough and stretch gently toward the corners. Proof 45 mins.",
                "Preheat oven to 425°F (220°C). Pour remaining olive oil over dough and dimple deeply with your fingertips.",
                "Scatter fresh rosemary and flaky sea salt over the top. Bake 25-28 minutes until deep golden and crisp."
            ]
        },
        {
            "title": "Heirloom Moong Dal Khichdi",
            "description": "The quintessential Ayurvedic comfort dish with yellow moong lentils, basmati rice, ghee, cumin, and mild spices.",
            "category": "Ayurvedic Mains",
            "servings": 4,
            "prep_time": "10 mins",
            "cook_time": "20 mins",
            "total_time": "30 mins",
            "calories": "285 kcal",
            "protein": "11g",
            "carbs": "46g",
            "fat": "6g",
            "fiber": "6g",
            "iron": "4.8 mg",
            "zinc": "2.2 mg",
            "ayurvedic_note": "Tridoshic | Supreme healing detox dish, kindles Agni gently.",
            "image_url": "/assets/placeholder_food.svg",
            "notes": "Cook until soft and porridge-like for the easiest assimilation and deepest nourishment.",
            "ingredients": [
                ("Basmati Rice (Chawal)", "1/2", "cup", "rinsed well"),
                ("Moong Dal (Yellow / Green)", "1/2", "cup", "rinsed well"),
                ("Pure Desi Cow Ghee", "2", "tbsp", "divided"),
                ("Cumin Seeds (Jeera)", "1", "tsp", "whole seeds"),
                ("Asafoetida (Hing)", "1/4", "tsp", "aromatic pinch"),
                ("Turmeric", "1/2", "tsp", "golden powder"),
                ("Fresh Ginger Root", "1", "tbsp", "finely grated"),
                ("Rock Salt (Saindhava Lavana)", "1", "tsp", "to taste"),
                ("Water", "4", "cups", "filtered")
            ],
            "instructions": [
                "Wash basmati rice and yellow moong dal together until water runs clear; soak for 15 minutes.",
                "In a heavy pot, heat 1.5 tbsp pure cow ghee. Add cumin seeds and let them splutter.",
                "Add asafoetida, grated fresh ginger, and turmeric; sauté for 30 seconds until fragrant.",
                "Add soaked rice and dal, stirring for 1 minute to coat grains in spiced ghee.",
                "Add 4 cups of water and rock salt. Bring to a boil, then cover and simmer on low for 20 minutes until creamy.",
                "Serve piping hot drizzled with remaining fresh ghee and a squeeze of fresh lemon."
            ]
        }
    ]

    for recipe_data in starter_recipes:
        create_recipe(recipe_data, conn=conn)


def get_all_recipes(search_query=None, category=None):
    """Retrieves all recipe cards with optional search filtering and category filtering."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT id, title, description, category, servings, yield_grams, prep_time, cook_time, total_time,
               calories, protein, carbs, fat, fiber, iron, zinc, ayurvedic_note, image_url, notes,
               created_at, updated_at
        FROM recipes
        WHERE 1=1
    """
    params = []

    if search_query and search_query.strip():
        term = f"%{search_query.strip()}%"
        query += """
            AND (
                title LIKE ? OR description LIKE ? OR notes LIKE ? OR ayurvedic_note LIKE ?
                OR id IN (SELECT recipe_id FROM ingredients WHERE name LIKE ?)
            )
        """
        params.extend([term, term, term, term, term])

    if category and category.strip() and category.lower() != "all":
        query += " AND category = ?"
        params.append(category.strip())

    query += " ORDER BY updated_at DESC, id DESC"

    cursor.execute(query, params)
    recipes_rows = cursor.fetchall()
    recipes = []

    for row in recipes_rows:
        recipe = dict(row)
        cursor.execute(
            "SELECT name, amount, unit, notes, order_index FROM ingredients WHERE recipe_id = ? ORDER BY order_index ASC, id ASC",
            (recipe["id"],)
        )
        recipe["ingredients"] = [dict(i) for i in cursor.fetchall()]

        cursor.execute(
            "SELECT step_number, instruction_text FROM instructions WHERE recipe_id = ? ORDER BY step_number ASC, id ASC",
            (recipe["id"],)
        )
        recipe["instructions"] = [dict(ins) for ins in cursor.fetchall()]
        recipes.append(recipe)

    conn.close()
    return recipes


def get_recipe_by_id(recipe_id):
    """Retrieves a single complete recipe card with its ingredients and instructions."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, description, category, servings, yield_grams, prep_time, cook_time, total_time,
               calories, protein, carbs, fat, fiber, iron, zinc, ayurvedic_note, image_url, notes,
               created_at, updated_at
        FROM recipes
        WHERE id = ?
    """, (recipe_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    recipe = dict(row)

    cursor.execute(
        "SELECT name, amount, unit, notes, order_index FROM ingredients WHERE recipe_id = ? ORDER BY order_index ASC, id ASC",
        (recipe_id,)
    )
    recipe["ingredients"] = [dict(i) for i in cursor.fetchall()]

    cursor.execute(
        "SELECT step_number, instruction_text FROM instructions WHERE recipe_id = ? ORDER BY step_number ASC, id ASC",
        (recipe_id,)
    )
    recipe["instructions"] = [dict(ins) for ins in cursor.fetchall()]

    conn.close()
    return recipe


def create_recipe(data, conn=None):
    """Creates a new recipe card with attached ingredients and instructions."""
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO recipes (
            title, description, category, servings, yield_grams, prep_time, cook_time, total_time,
            calories, protein, carbs, fat, fiber, iron, zinc, ayurvedic_note, image_url, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("title", "Untitled Recipe"),
        data.get("description", ""),
        data.get("category", "General"),
        int(data.get("servings", 4) or 4),
        max(0, int(data.get("yield_grams", 0) or 0)),
        data.get("prep_time", "15 mins"),
        data.get("cook_time", "30 mins"),
        data.get("total_time", "45 mins"),
        str(data.get("calories", "") or "").strip(),
        str(data.get("protein", "") or "").strip(),
        str(data.get("carbs", "") or "").strip(),
        str(data.get("fat", "") or "").strip(),
        str(data.get("fiber", "") or "").strip(),
        str(data.get("iron", "") or "").strip(),
        str(data.get("zinc", "") or "").strip(),
        str(data.get("ayurvedic_note", "") or "").strip(),
        data.get("image_url", ""),
        data.get("notes", "")
    ))

    recipe_id = cursor.lastrowid

    # Add ingredients
    ingredients = data.get("ingredients", [])
    for idx, ing in enumerate(ingredients):
        if isinstance(ing, (list, tuple)):
            name = ing[0] if len(ing) > 0 else ""
            amount = ing[1] if len(ing) > 1 else ""
            unit = ing[2] if len(ing) > 2 else ""
            notes = ing[3] if len(ing) > 3 else ""
        elif isinstance(ing, dict):
            name = ing.get("name", "")
            amount = ing.get("amount", "")
            unit = ing.get("unit", "")
            notes = ing.get("notes", "")
        else:
            name = str(ing)
            amount, unit, notes = "", "", ""

        if name and name.strip():
            cursor.execute("""
                INSERT INTO ingredients (recipe_id, name, amount, unit, notes, order_index)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (recipe_id, name.strip(), str(amount).strip(), str(unit).strip(), str(notes).strip(), idx))

    # Add instructions
    instructions = data.get("instructions", [])
    for idx, inst in enumerate(instructions):
        text = inst if isinstance(inst, str) else (inst.get("instruction_text", "") if isinstance(inst, dict) else str(inst))
        if text and text.strip():
            cursor.execute("""
                INSERT INTO instructions (recipe_id, step_number, instruction_text)
                VALUES (?, ?, ?)
            """, (recipe_id, idx + 1, text.strip()))

    conn.commit()
    if close_conn:
        conn.close()
        return get_recipe_by_id(recipe_id)
    return {"id": recipe_id}


def update_recipe(recipe_id, data):
    """Updates an existing recipe card with replacement of ingredients and instructions."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM recipes WHERE id = ?", (recipe_id,))
    if not cursor.fetchone():
        conn.close()
        return None

    cursor.execute("""
        UPDATE recipes SET
            title = ?,
            description = ?,
            category = ?,
            servings = ?,
            yield_grams = ?,
            prep_time = ?,
            cook_time = ?,
            total_time = ?,
            calories = ?,
            protein = ?,
            carbs = ?,
            fat = ?,
            fiber = ?,
            iron = ?,
            zinc = ?,
            ayurvedic_note = ?,
            image_url = ?,
            notes = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        data.get("title", "Untitled Recipe"),
        data.get("description", ""),
        data.get("category", "General"),
        int(data.get("servings", 4) or 4),
        max(0, int(data.get("yield_grams", 0) or 0)),
        data.get("prep_time", "15 mins"),
        data.get("cook_time", "30 mins"),
        data.get("total_time", "45 mins"),
        str(data.get("calories", "") or "").strip(),
        str(data.get("protein", "") or "").strip(),
        str(data.get("carbs", "") or "").strip(),
        str(data.get("fat", "") or "").strip(),
        str(data.get("fiber", "") or "").strip(),
        str(data.get("iron", "") or "").strip(),
        str(data.get("zinc", "") or "").strip(),
        str(data.get("ayurvedic_note", "") or "").strip(),
        data.get("image_url", ""),
        data.get("notes", ""),
        recipe_id
    ))

    # Replace ingredients
    cursor.execute("DELETE FROM ingredients WHERE recipe_id = ?", (recipe_id,))
    ingredients = data.get("ingredients", [])
    for idx, ing in enumerate(ingredients):
        if isinstance(ing, (list, tuple)):
            name = ing[0] if len(ing) > 0 else ""
            amount = ing[1] if len(ing) > 1 else ""
            unit = ing[2] if len(ing) > 2 else ""
            notes = ing[3] if len(ing) > 3 else ""
        elif isinstance(ing, dict):
            name = ing.get("name", "")
            amount = ing.get("amount", "")
            unit = ing.get("unit", "")
            notes = ing.get("notes", "")
        else:
            name = str(ing)
            amount, unit, notes = "", "", ""

        if name and name.strip():
            cursor.execute("""
                INSERT INTO ingredients (recipe_id, name, amount, unit, notes, order_index)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (recipe_id, name.strip(), str(amount).strip(), str(unit).strip(), str(notes).strip(), idx))

    # Replace instructions
    cursor.execute("DELETE FROM instructions WHERE recipe_id = ?", (recipe_id,))
    instructions = data.get("instructions", [])
    for idx, inst in enumerate(instructions):
        text = inst if isinstance(inst, str) else (inst.get("instruction_text", "") if isinstance(inst, dict) else str(inst))
        if text and text.strip():
            cursor.execute("""
                INSERT INTO instructions (recipe_id, step_number, instruction_text)
                VALUES (?, ?, ?)
            """, (recipe_id, idx + 1, text.strip()))

    conn.commit()
    conn.close()
    return get_recipe_by_id(recipe_id)


def delete_recipe(recipe_id):
    """Deletes a recipe card and its cascading ingredients and instructions."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


def get_prepopulated_ingredients(query=None, category=None):
    """Returns rich list of ingredients with multilingual names, nutrients, and Ayurvedic traits."""
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """
        SELECT id, name_en, name_hi, name_mr, category,
               calories_per_100g, protein, carbs, fat, fiber,
               zinc, iron, calcium, micronutrients,
               ayurvedic_significance, dosha_effect, taste_rasa, potency_virya,
               nutrition_basis
        FROM prepopulated_ingredients
        WHERE 1=1
    """
    params = []

    if query and query.strip():
        term = f"%{query.strip()}%"
        sql += """
            AND (
                name_en LIKE ? OR name_hi LIKE ? OR name_mr LIKE ?
                OR ayurvedic_significance LIKE ? OR micronutrients LIKE ?
                OR dosha_effect LIKE ? OR taste_rasa LIKE ?
            )
        """
        params.extend([term, term, term, term, term, term, term])

    if category and category.strip() and category.lower() != "all":
        sql += " AND category = ?"
        params.append(category.strip())

    sql += " ORDER BY category ASC, name_en ASC"

    cursor.execute(sql, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_ingredient_by_id(ing_id):
    """Retrieves single ingredient by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM prepopulated_ingredients WHERE id = ?", (ing_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def create_ingredient(data):
    """Creates a new custom ingredient in the pantry database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO prepopulated_ingredients (
            name_en, name_hi, name_mr, category,
            calories_per_100g, protein, carbs, fat, fiber,
            zinc, iron, calcium, micronutrients,
            ayurvedic_significance, dosha_effect, taste_rasa, potency_virya
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("name_en", "New Ingredient").strip(),
        data.get("name_hi", "").strip(),
        data.get("name_mr", "").strip(),
        data.get("category", "General").strip(),
        data.get("calories_per_100g", "").strip(),
        data.get("protein", "").strip(),
        data.get("carbs", "").strip(),
        data.get("fat", "").strip(),
        data.get("fiber", "").strip(),
        data.get("zinc", "").strip(),
        data.get("iron", "").strip(),
        data.get("calcium", "").strip(),
        data.get("micronutrients", "").strip(),
        data.get("ayurvedic_significance", "").strip(),
        data.get("dosha_effect", "").strip(),
        data.get("taste_rasa", "").strip(),
        data.get("potency_virya", "").strip()
    ))

    ing_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_ingredient_by_id(ing_id)


def update_ingredient(ing_id, data):
    """Updates an existing ingredient."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE prepopulated_ingredients SET
            name_en = ?,
            name_hi = ?,
            name_mr = ?,
            category = ?,
            calories_per_100g = ?,
            protein = ?,
            carbs = ?,
            fat = ?,
            fiber = ?,
            zinc = ?,
            iron = ?,
            calcium = ?,
            micronutrients = ?,
            ayurvedic_significance = ?,
            dosha_effect = ?,
            taste_rasa = ?,
            potency_virya = ?
        WHERE id = ?
    """, (
        data.get("name_en", "Ingredient").strip(),
        data.get("name_hi", "").strip(),
        data.get("name_mr", "").strip(),
        data.get("category", "General").strip(),
        data.get("calories_per_100g", "").strip(),
        data.get("protein", "").strip(),
        data.get("carbs", "").strip(),
        data.get("fat", "").strip(),
        data.get("fiber", "").strip(),
        data.get("zinc", "").strip(),
        data.get("iron", "").strip(),
        data.get("calcium", "").strip(),
        data.get("micronutrients", "").strip(),
        data.get("ayurvedic_significance", "").strip(),
        data.get("dosha_effect", "").strip(),
        data.get("taste_rasa", "").strip(),
        data.get("potency_virya", "").strip(),
        ing_id
    ))

    conn.commit()
    conn.close()
    return get_ingredient_by_id(ing_id)


def delete_ingredient(ing_id):
    """Deletes an ingredient."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM prepopulated_ingredients WHERE id = ?", (ing_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0
