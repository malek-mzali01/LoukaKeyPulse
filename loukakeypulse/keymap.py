# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import ctypes

from .keyinput import _foreground_hkl
from .winapi import u32


def _scan_vk(scan, hkl):
    try:
        return int(u32.MapVirtualKeyExW(scan, 3, hkl)) if hkl else 0
    except Exception:
        return 0


def _scan_label(scan, vk, hkl):
    state = (ctypes.c_ubyte * 256)()

    try:
        out = ctypes.create_unicode_buffer(8)
        count = u32.ToUnicodeEx(
            vk, scan, state, out, len(out), 0, hkl
        )

        if count > 0 and out.value:
            ch = out.value[0]

            if ch.isprintable() and not ch.isspace():
                return ch.upper() if ch.isalpha() else ch

    except Exception:
        pass

    try:
        vk_scan = int(
            u32.MapVirtualKeyExW(vk, 0, hkl)
        ) if hkl else 0

        if vk_scan:
            out = ctypes.create_unicode_buffer(8)
            count = u32.ToUnicodeEx(
                vk, vk_scan & 0xFF, state, out, len(out), 0, hkl
            )

            if count > 0 and out.value:
                ch = out.value[0]

                if ch.isprintable() and not ch.isspace():
                    return ch.upper() if ch.isalpha() else ch

    except Exception:
        pass

    if 0x30 <= vk <= 0x5A:
        return chr(vk)

    oem_fallback = {
        0xBA: ";", 0xBB: "=", 0xBC: ",", 0xBD: "-",
        0xBE: ".", 0xBF: "/", 0xC0: "`", 0xDB: "[",
        0xDC: "\\", 0xDD: "]", 0xDE: "'"
    }

    return oem_fallback.get(vk, _vkn(vk))


def _rows(hkl=None):
    def key(scan, width=1):
        vk = _scan_vk(scan, hkl)
        label = _scan_label(scan, vk, hkl) if vk else "?"
        return label, vk or None, width

    def fixed(label, vk, width=1):
        return label, vk, width

    number_scans = [0x29] + list(range(0x02, 0x0E))
    top = [key(sc) for sc in number_scans] + [key(0x0E, 2.0)]

    row1 = [fixed("Tab", None, 1.5)] + [
        key(sc) for sc in range(0x10, 0x1C)
    ]
    row1[-1] = key(0x1B, 1.0)

    row2 = [fixed("Caps", None, 1.75)] + [
        key(sc) for sc in range(0x1E, 0x29)
    ] + [fixed("Enter", None, 2.0)]

    row3 = [fixed("Shift", None, 2.25)] + [
        key(sc) for sc in range(0x2C, 0x36)
    ] + [fixed("Shift", None, 2.0)]

    row1[0] = ("Tab", None, 1.5)
    row2[0] = ("Caps", None, 1.75)
    row2[-1] = ("Enter", None, 2.0)
    row3[0] = ("Shift", None, 2.25)
    row3[-1] = ("Shift", None, 2.0)
    top[-1] = ("Back", None, 2.0)

    fn = list(_FR)

    bottom = [
        ("Ctrl", None, 1.4), ("Win", None, 1.2),
        ("Alt", None, 1.2), ("Space", None, 6.0),
        ("Alt", None, 1.2), ("Ctrl", None, 1.4)
    ]

    return [fn, top, row1, row2, row3, bottom]


_VKN = {
    0x08: "Back", 0x09: "Tab", 0x0D: "Enter",
    0x1B: "Esc", 0x20: "Space",
    0x21: "PgUp", 0x22: "PgDn", 0x23: "End",
    0x24: "Home", 0x25: "Left", 0x26: "Up",
    0x27: "Right", 0x28: "Down",
    0x2D: "Ins", 0x2E: "Del",
    0x70: "F1", 0x71: "F2", 0x72: "F3",
    0x73: "F4", 0x74: "F5", 0x75: "F6",
    0x76: "F7", 0x77: "F8", 0x78: "F9",
    0x79: "F10", 0x7A: "F11", 0x7B: "F12",
    0x05: "M4", 0x06: "M5"
}


def _vkn(vk):
    if vk in _VKN:
        return _VKN[vk]

    if 0x30 <= vk <= 0x5A:
        return chr(vk)

    return "0x%02X" % vk


def _display_key_name(vk):
    special = {
        0x08: "Backspace",
        0x09: "Tab",
        0x0D: "Enter",
        0x1B: "Esc",
        0x20: "Space",
        0x10: "Shift",
        0x11: "Ctrl",
        0x12: "Alt",
        0x5B: "Win",
        0x5C: "Win",
    }

    if vk in special:
        return special[vk]

    try:
        hkl = _foreground_hkl()
        scan = u32.MapVirtualKeyExW(vk, 0, hkl) if hkl else 0

        if scan:
            label = _scan_label(scan & 0xFF, vk, hkl)

            if label and not label.startswith("0x"):
                return label
    except Exception:
        pass

    return _vkn(vk)


_LBLVK = {
    "Esc": (0x1B,), "Tab": (0x09,), "Caps": (0x14,),
    "Back": (0x08,), "Enter": (0x0D,), "Space": (0x20,),
    "Shift": (0xA0, 0xA1), "Ctrl": (0xA2, 0xA3),
    "Alt": (0xA4, 0xA5), "Win": (0x5B, 0x5C)
}

_FR = [
    ("Esc", None, 1),
    ("F1", 0x70, 1), ("F2", 0x71, 1),
    ("F3", 0x72, 1), ("F4", 0x73, 1),
    ("F5", 0x74, 1), ("F6", 0x75, 1),
    ("F7", 0x76, 1), ("F8", 0x77, 1),
    ("F9", 0x78, 1), ("F10", 0x79, 1),
    ("F11", 0x7A, 1), ("F12", 0x7B, 1)
]
