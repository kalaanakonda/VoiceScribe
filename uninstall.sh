#!/usr/bin/env bash
# Uninstall VoiceScribe
set -euo pipefail

echo "Uninstalling VoiceScribe…"

# Stop if running
pkill -f "voicescribe" 2>/dev/null || true
sleep 1

rm -rf "$HOME/.voicescribe"
rm -rf "/Applications/VoiceScribe.app"

echo "✓ VoiceScribe removed."
echo "  Note: your data is still at ~/Library/Application Support/VoiceScribe/"
echo "  Delete that folder too if you want a clean slate."
