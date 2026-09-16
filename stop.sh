#!/usr/bin/env bash
# ==============================================================================
# Stop Script for Rustic Recipe Card Maker & Storage Web App
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PID_FILE="$SCRIPT_DIR/server.pid"
STOP_SENTINEL="$SCRIPT_DIR/.server_stop"
PORT="${PORT:-8080}"

echo "Stopping Rustic Recipe Card Server on port $PORT..."
# Signal stop via sentinel file
touch "$STOP_SENTINEL"

PID=""
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null || echo "")
fi

# Send SIGTERM if PID is available
if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
    kill -TERM "$PID" 2>/dev/null || true
fi

# Wait up to 3 seconds for server to process stop sentinel
ATTEMPTS=0
while [ $ATTEMPTS -lt 10 ]; do
    PORT_PID=$(lsof -ti:"$PORT" 2>/dev/null | head -n 1 || echo "")
    if [ -z "$PORT_PID" ]; then
        break
    fi
    sleep 0.3
    ATTEMPTS=$((ATTEMPTS + 1))
done

# Cleanup
rm -f "$PID_FILE"
rm -f "$STOP_SENTINEL"
echo "✅ Rustic Recipe Card Server stopped successfully."
exit 0
