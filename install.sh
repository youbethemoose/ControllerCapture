#!/bin/bash
set -e

APP_NAME="ControllerCapture"
DEST="$HOME/Desktop/$APP_NAME.app"

echo "==> ControllerCapture installer"
echo ""

# ── 1. Find Homebrew Python (arm64) ─────────────────────────────────────────
PYTHON=""
for candidate in \
    /opt/homebrew/bin/python3.13 \
    /opt/homebrew/bin/python3.12 \
    /opt/homebrew/bin/python3.11 \
    /opt/homebrew/bin/python3; do
    if [[ -x "$candidate" ]]; then
        PYTHON="$candidate"
        break
    fi
done

if [[ -z "$PYTHON" ]]; then
    echo "ERROR: No Homebrew Python found."
    echo "Install it with:  brew install python"
    exit 1
fi

echo "==> Using Python: $PYTHON ($($PYTHON --version))"

# ── 2. Install Python dependencies ──────────────────────────────────────────
echo "==> Installing dependencies (pygame, pynput, rumps)…"
"$PYTHON" -m pip install --quiet --upgrade pygame pynput rumps

# ── 3. Write the AppleScript launcher ───────────────────────────────────────
SCRIPT_DEST="$HOME/Library/Application Support/$APP_NAME/controller_capture.py"
mkdir -p "$(dirname "$SCRIPT_DEST")"
cp "$(dirname "$0")/controller_capture.py" "$SCRIPT_DEST"

TMPSCRIPT=$(mktemp /tmp/controllercapture_XXXX.applescript)
cat > "$TMPSCRIPT" <<APPLESCRIPT
on run
    set pythonPath to "$PYTHON"
    set scriptPath to (POSIX path of (path to application support folder from user domain)) & "$APP_NAME/controller_capture.py"
    do shell script "nohup " & pythonPath & " " & quoted form of scriptPath & " > /tmp/controllercapture.log 2>&1 &"
end run
APPLESCRIPT

# ── 4. Compile the .app ──────────────────────────────────────────────────────
echo "==> Building $APP_NAME.app…"
rm -rf "$DEST"
osacompile -o "$DEST" "$TMPSCRIPT"
rm "$TMPSCRIPT"

# Set LSUIElement so it runs without a Dock icon
/usr/libexec/PlistBuddy -c "Set :LSUIElement true" "$DEST/Contents/Info.plist" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Add :LSUIElement bool true" "$DEST/Contents/Info.plist"

# Clear quarantine so macOS doesn't block it
xattr -cr "$DEST"

echo ""
echo "✓ Installed to: $DEST"
echo ""
echo "Next steps:"
echo "  1. Double-click ControllerCapture on your Desktop to launch it."
echo "     (If macOS blocks it: right-click → Open)"
echo "  2. Look for 🎮 in your menu bar."
echo "  3. Go to System Settings → Privacy & Security → Accessibility"
echo "     and enable python3 (it will appear after the first launch)."
echo ""
