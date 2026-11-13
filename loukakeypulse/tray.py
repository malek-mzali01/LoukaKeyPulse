# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import ctypes
import ctypes.wintypes as W
import queue

from .config import APP_NAME, _res
from .winapi import NOTIFYICONDATAW, WNDCLASSW, WNDPROC, k32, shl, u32


TRAY_CLASS = "LoukaKeyPulseTrayWnd"

_tray_q = queue.Queue()
_tray_hwnd = None
WM_TRAY = 0x8001


def _tray_thread():
    global _tray_hwnd

    hinst = k32.GetModuleHandleW(None)
    cls = TRAY_CLASS
    created = int(u32.RegisterWindowMessageW("TaskbarCreated"))

    icon = u32.LoadImageW(None, _res("icon.ico"), 1, 16, 16, 0x10)
    if not icon:
        icon = u32.LoadIconW(None, 32512)

    def nid():
        d = NOTIFYICONDATAW()
        d.cbSize = ctypes.sizeof(d)
        d.hWnd = _tray_hwnd
        d.uID = 1
        d.uFlags = 0x7
        d.uCallbackMessage = WM_TRAY
        d.hIcon = icon
        d.szTip = APP_NAME
        return d

    def add():
        shl.Shell_NotifyIconW(0, ctypes.byref(nid()))

    def menu(hwnd):
        m = u32.CreatePopupMenu()
        u32.AppendMenuW(m, 0, 1, "Show")
        u32.AppendMenuW(m, 0, 4, "Check for updates")
        u32.AppendMenuW(m, 0, 2, "Quit")

        pt = W.POINT()
        u32.GetCursorPos(ctypes.byref(pt))
        u32.SetForegroundWindow(hwnd)

        cmd = u32.TrackPopupMenu(m, 0x182, pt.x, pt.y, 0, hwnd, None)
        u32.PostMessageW(hwnd, 0, 0, 0)
        u32.DestroyMenu(m)

        if cmd == 1:
            _tray_q.put("show")
        elif cmd == 2:
            _tray_q.put("quit")
        elif cmd == 4:
            _tray_q.put("update")

    def proc(hwnd, msg, wp, lp):
        if msg == WM_TRAY:
            ev = lp & 0xFFFF
            if ev in (0x202, 0x203):
                _tray_q.put("show")
            elif ev == 0x205:
                menu(hwnd)
            return 0

        if msg == created:
            add()
            return 0

        return u32.DefWindowProcW(hwnd, msg, wp, lp)

    cb = WNDPROC(proc)

    wc = WNDCLASSW()
    wc.lpfnWndProc = cb
    wc.hInstance = hinst
    wc.lpszClassName = cls
    u32.RegisterClassW(ctypes.byref(wc))

    _tray_hwnd = u32.CreateWindowExW(
        0, cls, cls, 0, 0, 0, 0, 0, None, None, hinst, None
    )

    add()

    msg = W.MSG()
    while u32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        u32.TranslateMessage(ctypes.byref(msg))
        u32.DispatchMessageW(ctypes.byref(msg))


def _tray_remove():
    if _tray_hwnd:
        d = NOTIFYICONDATAW()
        d.cbSize = ctypes.sizeof(d)
        d.hWnd = _tray_hwnd
        d.uID = 1
        shl.Shell_NotifyIconW(2, ctypes.byref(d))
