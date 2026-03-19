#!/bin/bash
set -e

APP_NAME="ControllerCapture"
DEST="$HOME/Desktop/$APP_NAME.app"
SUPPORT_DIR="$HOME/Library/Application Support/$APP_NAME"
VENV_DIR="$SUPPORT_DIR/venv"

echo "==> ControllerCapture installer"
echo ""

# ── 1. Find any Python 3.9+ ──────────────────────────────────────────────────
PYTHON=""
for candidate in \
    /opt/homebrew/bin/python3.13 \
    /opt/homebrew/bin/python3.12 \
    /opt/homebrew/bin/python3.11 \
    /opt/homebrew/bin/python3.10 \
    /opt/homebrew/bin/python3.9 \
    /opt/homebrew/bin/python3 \
    /usr/local/bin/python3 \
    "$(which python3 2>/dev/null)" \
    /usr/bin/python3; do
    if [[ -x "$candidate" ]]; then
        PYTHON="$candidate"
        break
    fi
done

if [[ -z "$PYTHON" ]]; then
    echo "ERROR: Python 3 not found."
    echo "Install it with:  brew install python"
    exit 1
fi

echo "==> Using Python: $PYTHON ($("$PYTHON" --version))"

# ── 2. Create a virtual environment ─────────────────────────────────────────
echo "==> Creating virtual environment…"
mkdir -p "$SUPPORT_DIR"
"$PYTHON" -m venv "$VENV_DIR"
VENV_PYTHON="$VENV_DIR/bin/python3"

# ── 3. Install dependencies into the venv ───────────────────────────────────
echo "==> Installing dependencies (pygame, pynput, rumps)…"
"$VENV_PYTHON" -m pip install --quiet --upgrade pip
"$VENV_PYTHON" -m pip install --quiet pygame pynput rumps

# ── 4. Copy the script ───────────────────────────────────────────────────────
cp "$(dirname "$0")/controller_capture.py" "$SUPPORT_DIR/controller_capture.py"

# ── 5. Build the AppleScript .app launcher ───────────────────────────────────
TMPSCRIPT=$(mktemp /tmp/controllercapture_XXXX.applescript)
cat > "$TMPSCRIPT" <<APPLESCRIPT
on run
    set pythonPath to "$VENV_PYTHON"
    set scriptPath to "$SUPPORT_DIR/controller_capture.py"
    do shell script "nohup " & pythonPath & " " & quoted form of scriptPath & " > /tmp/controllercapture.log 2>&1 &"
end run
APPLESCRIPT

echo "==> Building $APP_NAME.app…"
rm -rf "$DEST"
osacompile -o "$DEST" "$TMPSCRIPT"
rm "$TMPSCRIPT"

/usr/libexec/PlistBuddy -c "Set :LSUIElement true" "$DEST/Contents/Info.plist" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Add :LSUIElement bool true" "$DEST/Contents/Info.plist"

xattr -cr "$DEST"

echo ""
echo "✓ Installed to: $DEST"
echo ""
echo "Next steps:"
echo "  1. Double-click ControllerCapture on your Desktop to launch it."
echo "     (If macOS blocks it: right-click → Open)"
echo "  2. Look for 🎮 in your menu bar."
echo "  3. System Settings → Privacy & Security → Accessibility"
echo "     → enable python3 (appears after first launch)."
echo ""
