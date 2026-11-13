# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import threading


class St:
    def __init__(self):
        self.active = False
        self.interval_ms = 150
        self.targets = set()
        self.pause_vk = 0x7B
        self.spam_vks = set()
        self.spam_x1 = False
        self.spam_x2 = False
        self.blocked = {}


S = St()
_lock = threading.Lock()

_held = set()
_held_raw = set()
_held_x = {1: False, 2: False}

_cap_state = {"flag": False}
_cap_result = [None]
_cap_event = threading.Event()

_MODS = {
    "shift": {0x10, 0xA0, 0xA1},
    "ctrl": {0x11, 0xA2, 0xA3},
    "alt": {0x12, 0xA4, 0xA5}
}


def _mods_blocked(vk):
    b = S.blocked.get(vk)

    if not b:
        return False

    for m in b:
        if _held_raw & _MODS[m]:
            return True

    return False
