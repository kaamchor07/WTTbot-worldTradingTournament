#!/bin/bash
# Quick script to show latest signals

cd "/home/assifer/Desktop/New Folder"

# Find most recent signal file in logs folder
LATEST_SIGNAL=$(ls -t logs/signals_*.txt 2>/dev/null | head -1)

if [ -z "$LATEST_SIGNAL" ]; then
    echo "❌ No signal files found yet. Run scanner first!"
    exit 1
fi

echo "📊 Latest Signals from: $(basename $LATEST_SIGNAL)"
echo "═══════════════════════════════════════════════════"
cat "$LATEST_SIGNAL"
