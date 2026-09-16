#!/usr/bin/env bash
# ==============================================================================
# Start Script for Rustic Recipe Card Maker & Storage Web App
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE="$SCRIPT_DIR/server.pid"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/server.log"
PORT="${PORT:-8080}"
HOST="${HOST:-127.0.0.1}"

mkdir -p "$LOG_DIR"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null || echo "")
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "============================================================"
        echo " 📖 Rustic Recipe Card Server is ALREADY running!"
        echo " PID: $PID"
        echo " URL: http://$HOST:$PORT"
        echo "============================================================"
        exit 0
    else
        # Stale PID file
        rm -f "$PID_FILE"
    fi
fi

echo "Starting Rustic Recipe Card Server on http://$HOST:$PORT..."

# Start in background with unbuffered python output
nohup python3 -u server.py --host "$HOST" --port "$PORT" > "$LOG_FILE" 2>&1 &
SERVER_PID=$!
echo "$SERVER_PID" > "$PID_FILE"

# Wait a moment to ensure server started successfully
ATTEMPTS=0
MAX_ATTEMPTS=6
STARTED=0

while [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
    sleep 0.3
    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
        echo "❌ Server failed to start! Check logs at $LOG_FILE:"
        cat "$LOG_FILE"
        rm -f "$PID_FILE"
        exit 1
    fi

    # Check if process is alive and healthy
    if [ -s "$LOG_FILE" ] && grep -q "Server running at" "$LOG_FILE"; then
        STARTED=1
        break
    fi
    ATTEMPTS=$((ATTEMPTS + 1))
done

if [ $STARTED -eq 1 ] || kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "============================================================"
    echo " ✨ Rustic Recipe Card Maker & Storage is READY! ✨"
    echo "------------------------------------------------------------"
    echo " 🌐 Web App URL : http://$HOST:$PORT"
    echo " 🆔 Process PID : $SERVER_PID"
    echo " 📄 Log File    : $LOG_FILE"
    echo " 💾 Database    : $SCRIPT_DIR/data/recipes.db"
    echo "------------------------------------------------------------"
    echo " Use './stop.sh' to stop the server."
    echo " Use './status.sh' to check server health."
    echo "============================================================"
else
    echo "⚠️ Server started (PID: $SERVER_PID), check logs: tail -f $LOG_FILE"
fi
