# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import ctypes
import ctypes.wintypes as W
import time

from .winapi import (
    INJECTED,
    INPUT,
    KEYBDINPUT,
    KEYEVENTF_EXTENDEDKEY,
    KEYEVENTF_KEYUP,
    KEYEVENTF_SCANCODE,
    MOUSEEVENTF_XDOWN,
    MOUSEEVENTF_XUP,
    MOUSEINPUT,
    u32
)


_HKL_CACHE_TTL = 0.08
_hkl_cache_hwnd = None
_hkl_cache_value = None
_hkl_cache_at = 0.0


def _foreground_hkl():
    global _hkl_cache_hwnd, _hkl_cache_value, _hkl_cache_at

    now = time.monotonic()

    try:
        hwnd = u32.GetForegroundWindow()
    except Exception:
        hwnd = None

    if (
        hwnd == _hkl_cache_hwnd
        and now - _hkl_cache_at < _HKL_CACHE_TTL
        and _hkl_cache_value
    ):
        return _hkl_cache_value

    hkl = None

    try:
        if hwnd:
            pid = W.DWORD(0)
            tid = u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if tid:
                hkl = u32.GetKeyboardLayout(tid)
    except Exception:
        pass

    if not hkl:
        try:
            hkl = u32.GetKeyboardLayout(0)
        except Exception:
            hkl = None

    _hkl_cache_hwnd = hwnd
    _hkl_cache_value = hkl
    _hkl_cache_at = now

    return hkl


_scan_cache = {}


def _key_scan(vk):
    hkl = _foreground_hkl()
    ck = (hkl, vk)
    r = _scan_cache.get(ck)

    if r is None:
        scan = (
            u32.MapVirtualKeyExW(vk, 4, hkl)
            if hkl else u32.MapVirtualKeyW(vk, 0)
        )

        if scan:
            flags = KEYEVENTF_SCANCODE

            if scan & 0xFF00 == 0xE000:
                flags |= KEYEVENTF_EXTENDEDKEY

            r = (scan & 0xFF, flags)
        else:
            r = (0, 0)

        _scan_cache[ck] = r

    return r


def tap_key(vk: int):
    scan, fl = _key_scan(vk)
    arr = (INPUT * 2)()

    for i, f in enumerate((fl, fl | KEYEVENTF_KEYUP)):
        arr[i].type = 1
        arr[i].u.ki = KEYBDINPUT(vk, scan, f, 0, INJECTED)

    u32.SendInput(2, arr, ctypes.sizeof(INPUT))


def tap_xbtn(btn: int):
    arr = (INPUT * 2)()

    for i, f in enumerate((MOUSEEVENTF_XDOWN, MOUSEEVENTF_XUP)):
        arr[i].type = 0
        arr[i].u.mi = MOUSEINPUT(0, 0, btn, f, 0, INJECTED)

    u32.SendInput(2, arr, ctypes.sizeof(INPUT))


def _send_vk(vk, down):
    scan, fl = _key_scan(vk)
    arr = (INPUT * 1)()
    arr[0].type = 1
    arr[0].u.ki = KEYBDINPUT(
        vk, scan, fl | (0 if down else KEYEVENTF_KEYUP), 0, INJECTED
    )
    u32.SendInput(1, arr, ctypes.sizeof(INPUT))


def _press_enter():
    _send_vk(0x0D, True)
    time.sleep(0.05)
    _send_vk(0x0D, False)
