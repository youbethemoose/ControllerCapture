#!/usr/bin/env python3
"""
Xbox Controller → Capture One keyboard mapper
Runs as a menu bar app (🎮 in your menu bar).
"""

import json
import os
import time

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame
import rumps
from pynput.keyboard import Key, Controller

keyboard = Controller()

# ── Config persistence ────────────────────────────────────────────────────────

CONFIG_PATH = os.path.expanduser("~/.config/controllercapture/mappings.json")

BUTTON_NAMES = {
    0: "A", 1: "B", 2: "X", 3: "Y",
    4: "LB", 5: "RB", 6: "Back", 7: "Start",
    8: "L Stick", 9: "R Stick",
}

# Default shortcuts (all buttons → Cmd+K)
DEFAULT_SHORTCUTS = {
    0: "cmd+k",
    1: "cmd+k",
    2: "cmd+k",
    3: "cmd+k",
}

MODIFIER_PARSE = {
    "cmd": Key.cmd, "command": Key.cmd,
    "ctrl": Key.ctrl, "control": Key.ctrl,
    "shift": Key.shift,
    "alt": Key.alt, "option": Key.alt,
}

MODIFIER_DISPLAY = {
    Key.cmd: "⌘", Key.ctrl: "⌃", Key.shift: "⇧", Key.alt: "⌥",
}

MODIFIER_SERIALIZE = {
    Key.cmd: "cmd", Key.ctrl: "ctrl", Key.shift: "shift", Key.alt: "alt",
}


def parse_shortcut(text):
    """'cmd+shift+k' → [Key.cmd, Key.shift, 'k'], or None if invalid."""
    parts = [p.strip().lower() for p in text.strip().split("+") if p.strip()]
    if not parts:
        return None
    keys = []
    for part in parts:
        if part in MODIFIER_PARSE:
            keys.append(MODIFIER_PARSE[part])
        elif len(part) == 1:
            keys.append(part)
        else:
            return None
    return keys or None


def keys_to_display(keys):
    """[Key.cmd, 'k'] → '⌘K'"""
    parts = []
    for k in keys:
        if k in MODIFIER_DISPLAY:
            parts.append(MODIFIER_DISPLAY[k])
        else:
            parts.append(str(k).upper())
    return "".join(parts)


def keys_to_str(keys):
    """[Key.cmd, 'k'] → 'cmd+k' (for JSON storage)"""
    parts = []
    for k in keys:
        if k in MODIFIER_SERIALIZE:
            parts.append(MODIFIER_SERIALIZE[k])
        else:
            parts.append(str(k))
    return "+".join(parts)


def load_config():
    """Load saved mappings, falling back to defaults."""
    mappings = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                raw = json.load(f)
            for idx_str, shortcut in raw.items():
                idx = int(idx_str)
                keys = parse_shortcut(shortcut)
                if keys:
                    mappings[idx] = keys
        except Exception:
            pass

    # Fill missing buttons from defaults
    for idx, shortcut in DEFAULT_SHORTCUTS.items():
        if idx not in mappings:
            mappings[idx] = parse_shortcut(shortcut)

    return mappings


def save_config(mappings):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump({str(k): keys_to_str(v) for k, v in mappings.items()}, f, indent=2)


# ── Key press ─────────────────────────────────────────────────────────────────

def press_combo(keys):
    for k in keys:
        keyboard.press(k)
    time.sleep(0.05)
    for k in reversed(keys):
        keyboard.release(k)


# ── App ───────────────────────────────────────────────────────────────────────

class ControllerApp(rumps.App):
    def __init__(self):
        super().__init__("🎮", quit_button="Quit ControllerCapture")
        self.joystick = None
        self.mappings = load_config()
        self._build_menu()
        pygame.init()
        pygame.joystick.init()

    # ── Menu ──────────────────────────────────────────────────────────────────

    def _build_menu(self):
        self.menu.clear()
        for idx in sorted(BUTTON_NAMES):
            name = BUTTON_NAMES[idx]
            keys = self.mappings.get(idx)
            label = f"{name}:  {keys_to_display(keys)}" if keys else f"{name}:  (none)"
            item = rumps.MenuItem(label, callback=self._make_configure_cb(idx))
            self.menu.add(item)
        self.menu.add(rumps.separator)

    def _make_configure_cb(self, idx):
        def callback(_):
            self._configure_button(idx)
        return callback

    # ── Configure dialog ──────────────────────────────────────────────────────

    def _configure_button(self, idx):
        name = BUTTON_NAMES[idx]
        current = self.mappings.get(idx)
        current_str = keys_to_str(current) if current else ""

        win = rumps.Window(
            title=f"Configure {name} Button",
            message=(
                "Enter a shortcut (e.g. cmd+k, cmd+shift+z, ctrl+space)\n"
                "Leave blank to disable this button."
            ),
            default_text=current_str,
            ok="Save",
            cancel="Cancel",
            dimensions=(260, 24),
        )
        response = win.run()

        if response.clicked:
            text = response.text.strip()
            if text == "":
                self.mappings.pop(idx, None)
            else:
                keys = parse_shortcut(text)
                if keys:
                    self.mappings[idx] = keys
                else:
                    rumps.alert(
                        title="Invalid shortcut",
                        message=f'Could not parse "{text}".\nUse format like: cmd+k or cmd+shift+z',
                    )
                    return
            save_config(self.mappings)
            self._build_menu()

    # ── Controller polling ────────────────────────────────────────────────────

    @rumps.timer(0.01)
    def poll(self, _):
        pygame.event.pump()

        count = pygame.joystick.get_count()
        if count == 0:
            if self.joystick is not None:
                self.joystick = None
                self.title = "🎮❌"
            return

        if self.joystick is None:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            self.title = "🎮"

        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                keys = self.mappings.get(event.button)
                if keys:
                    press_combo(keys)


if __name__ == "__main__":
    ControllerApp().run()
