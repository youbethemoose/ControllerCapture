# ControllerCapture

Ever wish you could use an Xbox controller to snap a photo in Capture One? Now you don't have to Google and install random apps to do so — I built this for scanning film and shooting still life. Enjoy!

A tiny macOS menu bar app that maps Xbox One controller buttons to keyboard shortcuts — built for [Capture One](https://www.captureone.com/) tethered shooting, but works with any app.

**Default mapping:** A / B / X / Y → `⌘K` (Capture One: Capture)

---

## Requirements

- macOS (Apple Silicon recommended)
- [Homebrew](https://brew.sh) with Python 3.11+
  ```bash
  brew install python
  ```
- Xbox One controller (USB or Bluetooth)

---

## Install

```bash
git clone https://github.com/youbethemoose/ControllerCapture.git
cd ControllerCapture
./install.sh
```

The script will:
1. Install Python dependencies (`pygame`, `pynput`, `rumps`)
2. Build `ControllerCapture.app` onto your Desktop

---

## First Launch

1. Double-click **ControllerCapture** on your Desktop
   - If macOS blocks it: **right-click → Open**
2. Look for **🎮** in your menu bar — that means it's running
   - **🎮❌** means no controller is detected
3. Go to **System Settings → Privacy & Security → Accessibility**
   and toggle on `python3` (it appears after the first launch attempt)

---

## Customizing Button Mappings

Open `controller_capture.py` and edit the `BUTTON_MAP` dictionary:

```python
BUTTON_MAP = {
    0: ("A → Cmd+K", [Key.cmd, 'k']),
    1: ("B → Cmd+K", [Key.cmd, 'k']),
    2: ("X → Cmd+K", [Key.cmd, 'k']),
    3: ("Y → Cmd+K", [Key.cmd, 'k']),

    # More examples:
    # 4: ("LB → Cmd+Z",       [Key.cmd, 'z']),
    # 5: ("RB → Cmd+Shift+Z", [Key.cmd, Key.shift, 'z']),
    # 6: ("Back → Cmd+[",     [Key.cmd, '[']),
    # 7: ("Start → Cmd+]",    [Key.cmd, ']']),
}
```

After editing, re-run `./install.sh` to rebuild the app.

### Xbox Button Indices

| Index | Button  |
|-------|---------|
| 0     | A       |
| 1     | B       |
| 2     | X       |
| 3     | Y       |
| 4     | LB      |
| 5     | RB      |
| 6     | Back    |
| 7     | Start   |
| 8     | L Stick |
| 9     | R Stick |

---

## Quitting

Click **🎮** in the menu bar → **Quit ControllerCapture**

---

## License

MIT
