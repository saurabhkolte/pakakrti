# Pākakṛti — Rustic Recipe Card Maker & Storage

A self-contained web application for crafting, editing, storing, printing, and exporting recipe index cards with a warm, authentic antique book page aesthetic.

---

## 🌟 Key Features

- **Antique Book Page Aesthetic**:
  - Aged ivory parchment textures, deckled borders, warm sepia ink, and classic Victorian flourishes (❦ ❧ ✦).
  - Elegant serif typography tailored for culinary keepsakes and family heirlooms.

- **Scalable 2-Column Index Card Layout**:
  - **Left Column**: Uploadable recipe photograph with vintage frame, recipe title, servings badge, prep time, and total time.
  - **Right Column**: Top section with ingredient list (quantities, units, notes), bottom section with numbered method & cooking directions.

- **Multiple Card Size Presets & Zoom**:
  - **3" × 5"** Classic index card format.
  - **4" × 6"** Large recipe card format.
  - **5" × 7"** Keepsake display format.
  - Live zoom scaling slider (60% to 130%).

- **Card Maker with Live Real-Time Preview**:
  - As you type ingredients, title, instructions, or adjust cooking times, the card updates in real time.
  - Prepopulated ingredient autocomplete dictionary with 116+ common pantry staples across categories (Baking, Dairy, Herbs, Spices, Produce, Meats, Oils).
  - Drag-and-drop or click-to-upload recipe photos.

- **Single-File SQLite Storage**:
  - Stored locally in `data/recipes.db` with SQLite WAL mode.
  - Pre-seeded with 6 starter recipes (*Grandma's Chocolate Chip Cookies*, *Artisan Rosemary Focaccia*, *Roman Spaghetti Carbonara*, *French Onion Soup*, *Creamy Tuscan Garlic Chicken*, and *Old-Fashioned Apple Pie*).

- **Export & Print**:
  - **Export as JPG**: Generates a high-resolution (300 DPI index card print ready) JPEG image download with a single click.
  - **Printable**:
    - Direct printing onto standard **3" × 5"** or **4" × 6"** index card stock.
    - Standard US Letter / A4 paper printing with cutting guidelines and trim marks.

- **Zero External Runtime Dependencies**:
  - Powered strictly by Python 3's built-in standard library (`http.server`, `sqlite3`, `json`).
  - No `pip install` or external internet connection needed.

---

## 🚀 Quick Start

### 1. Start Server
Run the startup script:
```bash
./start.sh
```
The server will initialize SQLite (if not already created) and launch in the background. Open your browser to:
**[http://127.0.0.1:8080](http://127.0.0.1:8080)**

### 2. Check Server Status
Check whether the server is running, along with database statistics:
```bash
./status.sh
```

### 3. Stop Server
Stop the server cleanly:
```bash
./stop.sh
```

---

## 📁 Project Structure

```
pakakrti/
├── server.py              # Pure Python 3 HTTP Server & REST API
├── db.py                  # SQLite database manager, schemas & seeder
├── start.sh               # Background start script with PID management
├── stop.sh                # Clean shutdown script with sentinel trigger
├── status.sh              # Server and database health checker
├── data/
│   └── recipes.db         # Single-file SQLite database (auto-created)
├── logs/
│   └── server.log         # Server runtime logs
├── uploads/               # Locally stored user-uploaded recipe images
├── public/                # Static frontend assets
│   ├── index.html         # Main Web application UI
│   ├── css/
│   │   └── rustic-theme.css # Vintage book styling, 2-col card & print rules
│   ├── js/
│   │   ├── app.js         # Client state, live sync & autocomplete
│   │   └── exporter.js    # High-res JPG export & card print engine
│   └── assets/            # Vintage recipe SVGs and parchment textures
└── README.md
```

---

## 🖨️ Printing Instructions

1. In the **Recipe Card Maker**, click **🖨️ Print Card**.
2. Select your print format:
   - **Direct 3" × 5" Index Card Stock**: Set your printer tray to index card size. The card will print full bleed without margins.
   - **Standard US Letter / A4 with Cutting Guidelines**: Prints centered on normal letter paper with dashed cutting lines around the card.
3. In the browser print dialog, ensure **Background graphics** is checked under *More settings* so the vintage parchment paper texture prints.
