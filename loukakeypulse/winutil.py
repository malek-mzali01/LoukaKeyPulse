# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import ctypes
import ctypes.wintypes as W
import os
import time

from .state import S
from .winapi import (
    GWL_EXSTYLE,
    GWL_STYLE,
    SWP_FRAMECHANGED,
    SWP_NOMOVE,
    SWP_NOSIZE,
    WS_CAPTION,
    WS_EX_APPWINDOW,
    WS_EX_TOOLWINDOW,
    WS_MAXIMIZEBOX,
    WS_MINIMIZEBOX,
    WS_SYSMENU,
    WS_THICKFRAME,
    dwm,
    k32,
    u32
)


def _fg_is(pid):
    try:
        h = u32.GetForegroundWindow()
        return bool(h) and _hwnd_pid(h) == pid
    except Exception:
        return False


def _focus_window(hwnd, pid):
    if u32.IsIconic(hwnd):
        u32.ShowWindow(hwnd, 9)

    u32.SetForegroundWindow(hwnd)

    for _ in range(10):
        time.sleep(0.05)

        if _fg_is(pid):
            return True

    try:
        fg = u32.GetForegroundWindow()
        tid_fg = u32.GetWindowThreadProcessId(fg, None)
        tid_me = k32.GetCurrentThreadId()

        u32.AttachThreadInput(tid_me, tid_fg, True)
        u32.SetForegroundWindow(hwnd)
        u32.AttachThreadInput(tid_me, tid_fg, False)
    except Exception:
        pass

    time.sleep(0.3)
    return _fg_is(pid)


def _fg_title() -> str:
    hwnd = u32.GetForegroundWindow()
    n = u32.GetWindowTextLengthW(hwnd)
    b = ctypes.create_unicode_buffer(n + 1)
    u32.GetWindowTextW(hwnd, b, n + 1)
    return b.value


_FG_EXE_CACHE_TTL = 0.20
_fg_exe_cache_hwnd = None
_fg_exe_cache_value = ""
_fg_exe_cache_at = 0.0


def _pid_path(pid):
    h = k32.OpenProcess(0x1000, False, pid)

    if not h:
        return ""

    try:
        buf = ctypes.create_unicode_buffer(1024)
        n = W.DWORD(1024)

        ok = k32.QueryFullProcessImageNameW(
            h, 0, buf, ctypes.byref(n)
        )

        return buf.value if ok else ""

    finally:
        k32.CloseHandle(h)


def _hwnd_pid(hwnd):
    pid = W.DWORD(0)
    u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def _fg_exe() -> str:
    global _fg_exe_cache_hwnd
    global _fg_exe_cache_value
    global _fg_exe_cache_at

    now = time.monotonic()

    try:
        hwnd = u32.GetForegroundWindow()

        if (
            hwnd == _fg_exe_cache_hwnd
            and now - _fg_exe_cache_at < _FG_EXE_CACHE_TTL
        ):
            return _fg_exe_cache_value

        pid = _hwnd_pid(hwnd) if hwnd else 0
        path = _pid_path(pid) if pid else ""
        exe = os.path.basename(path).lower() if path else ""

        _fg_exe_cache_hwnd = hwnd
        _fg_exe_cache_value = exe
        _fg_exe_cache_at = now

        return exe

    except Exception:
        return ""


def _win_ok() -> bool:
    t = S.targets
    return (not t) or (_fg_exe() in t)


_ME = os.getpid()


def _spam_win_ok() -> bool:
    try:
        h = u32.GetForegroundWindow()

        if h and _hwnd_pid(h) == _ME:
            return False
    except Exception:
        pass

    return _win_ok()


_SKIP = {
    "applicationframehost.exe", "textinputhost.exe",
    "searchhost.exe", "shellexperiencehost.exe",
    "startmenuexperiencehost.exe"
}


def _list_apps():
    out = {}
    me = os.getpid()

    EP = ctypes.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)

    def cb(h, _):
        try:
            if not u32.IsWindowVisible(h):
                return True

            n = u32.GetWindowTextLengthW(h)

            if not n:
                return True

            ex = u32.GetWindowLongW(h, GWL_EXSTYLE)

            if (ex & WS_EX_TOOLWINDOW) and not (ex & WS_EX_APPWINDOW):
                return True

            c = ctypes.c_int(0)
            dwm.DwmGetWindowAttribute(h, 14, ctypes.byref(c), 4)

            if c.value:
                return True

            pid = _hwnd_pid(h)

            if not pid or pid == me:
                return True

            path = _pid_path(pid)

            if not path:
                return True

            exe = os.path.basename(path).lower()

            if exe in _SKIP or exe in out:
                return True

            b = ctypes.create_unicode_buffer(n + 1)
            u32.GetWindowTextW(h, b, n + 1)

            out[exe] = dict(
                exe=exe, path=path, title=b.value.strip()
            )

        except Exception:
            pass

        return True

    u32.EnumWindows(EP(cb), 0)
    return list(out.values())


def _remove_titlebar(hwnd):
    style = u32.GetWindowLongW(hwnd, GWL_STYLE)
    style &= ~(
        WS_CAPTION | WS_THICKFRAME | WS_SYSMENU
        | WS_MINIMIZEBOX | WS_MAXIMIZEBOX
    )

    u32.SetWindowLongW(hwnd, GWL_STYLE, style)

    ex = u32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    ex = (ex & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW

    u32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex)

    u32.SetWindowPos(
        hwnd, None, 0, 0, 0, 0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_FRAMECHANGED
    )
