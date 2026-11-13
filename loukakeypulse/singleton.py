# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import ctypes

from .config import APP_NAME
from .tray import TRAY_CLASS, WM_TRAY
from .winapi import k32, u32


MUTEX_NAME = "Local\\LoukaKeyPulse.SingleInstance"

_handle = None


def acquire():
    global _handle

    handle = k32.CreateMutexW(None, False, MUTEX_NAME)
    err = ctypes.get_last_error()

    if not handle or err in (5, 183):
        return False

    _handle = handle
    return True


def notify_existing():
    hwnd = u32.FindWindowW(TRAY_CLASS, None)
    shown = False

    if hwnd:
        shown = bool(u32.PostMessageW(hwnd, WM_TRAY, 0, 0x202))

    if not shown:
        u32.MessageBoxW(
            None, APP_NAME + " is already running. Check the system tray.",
            APP_NAME, 0x40
        )


def release():
    global _handle

    if _handle:
        k32.CloseHandle(_handle)
        _handle = None
