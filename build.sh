#!/bin/bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

echo "== Cleaning previous build artifacts =="
rm -rf build dist

echo "== Building PBHB.exe (app.spec) =="
pyinstaller app.spec --distpath dist --workpath build

echo "== Building updater.exe (tools/updater.spec) =="
pyinstaller tools/updater.spec --distpath dist --workpath build

echo "== Assembling release structure (inside dist/) =="
VERSION="DEV"

FOLDER="dist/PBHB"
mkdir -p "$FOLDER/_internal/tools"

mv "dist/PBHB.exe" "$FOLDER/PBHB.exe"
printf '%s' "$VERSION" > "$FOLDER/_internal/version"
mv "dist/updater.exe" "$FOLDER/_internal/tools/updater.exe"

echo "Done."
echo ""
echo "Press any key to exit..."
read -n 1 -s