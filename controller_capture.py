#!/usr/bin/env python3
"""
Xbox Controller → Capture One keyboard mapper
Runs as a menu bar app (🎮 in your menu bar).
"""

import os
import time

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import json
import pygame
import rumps
from pynput.keyboard import Key, Controller

keyboard = Controller()

# ── Config ────────────────────────────────────────────────────────────────────

CONFIG_PATH = os.path.expanduser("~/.config/controllercapture/mappings.json")

# Human-readable names for menu display.
# These are defaults — real indices are detected per-controller.
BUTTON_NAMES = {
    0: "Button 0 (A)",
    1: "Button 1 (B)",
    2: "Button 2 (X)",
    3: "Button 3 (Y)",
    4: "Button 4 (LB)",
    5: "Button 5 (RB)",
    6: "Button 6 (Back)",
    7: "Button 7 (Start)",
    8: "Button 8 (L Stick)",
    9: "Button 9 (R Stick)",
}

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

# Special non-modifier keys by name
SPECIAL_KEYS = {
    "space": Key.space,
    "enter": Key.enter, "return": Key.enter,
    "tab": Key.tab,
    "esc": Key.esc, "escape": Key.esc,
    "delete": Key.delete,
    "backspace": Key.backspace,
    "up": Key.up, "down": Key.down,
    "left": Key.left, "right": Key.right,
    "f1": Key.f1, "f2": Key.f2, "f3": Key.f3,
    "f4": Key.f4, "f5": Key.f5, "f6": Key.f6,
    "f7": Key.f7, "f8": Key.f8, "f9": Key.f9,
    "f10": Key.f10, "f11": Key.f11, "f12": Key.f12,
}

MODIFIER_DISPLAY = {
    Key.cmd: "⌘", Key.ctrl: "⌃", Key.shift: "⇧", Key.alt: "⌥",
}

MODIFIER_SERIALIZE = {
    Key.cmd: "cmd", Key.ctrl: "ctrl", Key.shift: "shift", Key.alt: "alt",
}

SPECIAL_SERIALIZE = {v: k for k, v in SPECIAL_KEYS.items() if k == list(SPECIAL_KEYS.keys())[list(SPECIAL_KEYS.values()).index(v)]}


def parse_shortcut(text):
    """'cmd+shift+k' or 'cmd+space' → list of keys, or None if invalid."""
    parts = [p.strip().lower() for p in text.strip().split("+") if p.strip()]
    if not parts:
        return None
    keys = []
    for part in parts:
        if part in MODIFIER_PARSE:
            keys.append(MODIFIER_PARSE[part])
        elif part in SPECIAL_KEYS:
            keys.append(SPECIAL_KEYS[part])
        elif len(part) == 1:
            keys.append(part)
        else:
            return None
    return keys or None


def keys_to_display(keys):
    parts = []
    for k in keys:
        if k in MODIFIER_DISPLAY:
            parts.append(MODIFIER_DISPLAY[k])
        elif k in SPECIAL_SERIALIZE:
            parts.append(SPECIAL_SERIALIZE[k].capitalize())
        else:
            parts.append(str(k).upper())
    return "".join(parts)


def keys_to_str(keys):
    parts = []
    for k in keys:
        if k in MODIFIER_SERIALIZE:
            parts.append(MODIFIER_SERIALIZE[k])
        elif k in SPECIAL_SERIALIZE:
            parts.append(SPECIAL_SERIALIZE[k])
        else:
            parts.append(str(k))
    return "+".join(parts)


def load_config():
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
        self.detect_mode = False
        self._build_menu()
        pygame.init()
        pygame.joystick.init()

    # ── Menu ──────────────────────────────────────────────────────────────────

    def _build_menu(self):
        self.menu.clear()

        # Detect mode toggle
        detect_label = "🔍 Stop Detecting  (press a button)" if self.detect_mode else "🔍 Detect Button Indices"
        self.menu.add(rumps.MenuItem(detect_label, callback=self._toggle_detect))
        self.menu.add(rumps.separator)

        for idx in sorted(BUTTON_NAMES):
            name = BUTTON_NAMES[idx]
            keys = self.mappings.get(idx)
            label = f"{name}:  {keys_to_display(keys)}" if keys else f"{name}:  (none)"
            self.menu.add(rumps.MenuItem(label, callback=self._make_configure_cb(idx)))

        self.menu.add(rumps.separator)

    def _make_configure_cb(self, idx):
        def callback(_):
            self._configure_button(idx)
        return callback

    def _toggle_detect(self, _):
        self.detect_mode = not self.detect_mode
        self.title = "🔍" if self.detect_mode else "🎮"
        self._build_menu()

    # ── Configure dialog ──────────────────────────────────────────────────────

    def _configure_button(self, idx):
        name = BUTTON_NAMES[idx]
        current = self.mappings.get(idx)
        current_str = keys_to_str(current) if current else ""

        win = rumps.Window(
            title=f"Configure {name}",
            message=(
                "Enter a shortcut, e.g.:\n"
                "  cmd+k   cmd+shift+z   ctrl+space\n"
                "  cmd+f1  cmd+enter     cmd+left\n\n"
                "Leave blank to disable this button.\n"
                "(Tip: use 🔍 Detect to find the right button index)"
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
                        message=(
                            f'Could not parse "{text}".\n\n'
                            "Valid modifiers: cmd, ctrl, shift, alt\n"
                            "Special keys: space, enter, esc, tab,\n"
                            "  delete, up, down, left, right, f1–f12\n"
                            "Example: cmd+shift+z"
                        ),
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
            self.title = "🔍" if self.detect_mode else "🎮"

        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                if self.detect_mode:
                    rumps.notification(
                        title="Button Detected",
                        subtitle=f"Index: {event.button}",
                        message=f"Use 'Button {event.button}' when configuring this button.",
                    )
                else:
                    keys = self.mappings.get(event.button)
                    if keys:
                        press_combo(keys)


if __name__ == "__main__":
    ControllerApp().run()
