#!/usr/bin/env bash
# ==============================================================================
# Status Script for Rustic Recipe Card Maker & Storage Web App
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE="$SCRIPT_DIR/server.pid"
PORT="${PORT:-8080}"
HOST="${HOST:-127.0.0.1}"

echo "============================================================"
echo " 🔍 Rustic Recipe Card Maker - Status Check"
echo "============================================================"

RUNNING=0
PID=""

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null || echo "")
fi

# Check via kill -0 or lsof on port
PORT_PID=$(lsof -ti:"$PORT" 2>/dev/null | head -n 1 || echo "")

if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
    RUNNING=1
elif [ -n "$PORT_PID" ]; then
    RUNNING=1
    PID="$PORT_PID"
fi

if [ $RUNNING -eq 1 ]; then
    echo " 🟢 Server Status : RUNNING"
    echo " 🆔 Process PID    : $PID"
    echo " 🌐 Web Address   : http://$HOST:$PORT"

    # Query DB stats using python helper
    DB_STATS=$(python3 -c "
import sqlite3, os
from pathlib import Path
db_path = Path('data/recipes.db')
if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM recipes')
    rc = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM prepopulated_ingredients')
    ic = c.fetchone()[0]
    size_kb = os.path.getsize(db_path) / 1024
    print(f'{rc} recipes stored | {ic} pantry ingredients | DB size: {size_kb:.1f} KB')
else:
    print('Database not yet created')
" 2>/dev/null || echo "Unknown")

    echo " 📊 Database Info  : $DB_STATS"
    echo " 📄 Log File       : logs/server.log"
else
    echo " 🔴 Server Status : NOT RUNNING"
    echo " Run './start.sh' to start the server."
fi
echo "============================================================"
