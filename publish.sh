#!/bin/bash
# publish.sh — Push weekly Clarkston Ward program to GitHub Pages
# Usage: ./publish.sh
# Run this from the clarkstonward folder after updating index.html and program.pdf

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Check for uncommitted changes
if git diff --quiet && git diff --cached --quiet; then
  echo "Nothing to publish — no changes detected."
  exit 0
fi

# Build a commit message with today's date
DATE=$(date +"%B %d, %Y")
SUNDAY=$(date -v+Sun +"%B %d, %Y" 2>/dev/null || date -d "next Sunday" +"%B %d, %Y" 2>/dev/null || echo "$DATE")

echo "Publishing program for $SUNDAY..."

git add -A
git commit -m "Program update — $SUNDAY"
git push

echo ""
echo "✓ Published! Live at https://godfrea2407.github.io/clarkstonward/"
echo "  (GitHub Pages rebuilds in ~60 seconds)"
echo ""
echo "  HTML:  https://godfrea2407.github.io/clarkstonward/"
echo "  PDF:   https://godfrea2407.github.io/clarkstonward/pdf.html"
