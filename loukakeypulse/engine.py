# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import ctypes
import ctypes.wintypes as W
import math
import queue
import time

from .config import _log
from .keyinput import tap_key, tap_xbtn
from .state import (
    S,
    _cap_event,
    _cap_result,
    _cap_state,
    _held,
    _held_raw,
    _held_x,
    _lock,
    _mods_blocked
)
from .winapi import (
    HOOKPROC,
    INJECTED,
    KBDLLHOOKSTRUCT,
    MSLLHOOKSTRUCT,
    WH_KEYBOARD_LL,
    WH_MOUSE_LL,
    WM_KEYDOWN,
    WM_KEYUP,
    WM_SYSKEYDOWN,
    WM_SYSKEYUP,
    WM_XBUTTONDOWN,
    WM_XBUTTONUP,
    XBUTTON1,
    XBUTTON2,
    _vp,
    k32,
    u32
)
from .winutil import _spam_win_ok
from .wowchat import _chat_open


_wake = k32.CreateEventW(None, False, False, None)
_press_q = queue.SimpleQueue()


def _spam_ok(vk):
    return bool(
        S.active and vk in S.spam_vks
        and not _mods_blocked(vk) and _spam_win_ok()
        and not _chat_open()
    )


def _make_hooks():
    def kb_proc(nCode, wParam, lParam):

        if nCode >= 0:
            try:
                kb = ctypes.cast(
                    lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)
                ).contents

                if kb.dwExtraInfo != INJECTED:
                    vk = int(kb.vkCode)

                    if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                        repeat = vk in _held_raw
                        handled = False

                        if _cap_state["flag"] and not repeat:
                            _cap_result[0] = vk
                            _cap_state["flag"] = False
                            _cap_event.set()
                            handled = True

                        elif vk == S.pause_vk and not repeat:
                            with _lock:
                                S.active = not S.active
                            handled = True

                        _held_raw.add(vk)

                        if not handled and vk in S.spam_vks:
                            if vk in _held:
                                return 1

                            if not repeat and _spam_ok(vk):
                                _held.add(vk)
                                _press_q.put(("k", vk))
                                k32.SetEvent(_wake)
                                return 1

                    elif wParam in (WM_KEYUP, WM_SYSKEYUP):
                        _held_raw.discard(vk)

                        if vk in _held:
                            _held.discard(vk)
                            return 1

            except Exception:
                pass

        return u32.CallNextHookEx(None, nCode, wParam, lParam)

    def ms_proc(nCode, wParam, lParam):

        if nCode >= 0:
            try:
                ms = ctypes.cast(
                    lParam, ctypes.POINTER(MSLLHOOKSTRUCT)
                ).contents

                if (
                    ms.dwExtraInfo != INJECTED
                    and wParam in (WM_XBUTTONDOWN, WM_XBUTTONUP)
                ):
                    which = (ms.mouseData >> 16) & 0xFFFF

                    if which in (1, 2):
                        dn = wParam == WM_XBUTTONDOWN
                        held = _held_x[which]
                        want = S.spam_x1 if which == 1 else S.spam_x2

                        if dn:
                            if held:
                                return 1

                            if want and S.active and _spam_win_ok() and not _chat_open():
                                _held_x[which] = True

                                _press_q.put(("x", which))
                                k32.SetEvent(_wake)
                                return 1

                        elif held:
                            _held_x[which] = False

                            return 1

            except Exception:
                pass

        return u32.CallNextHookEx(None, nCode, wParam, lParam)

    cb_kb = HOOKPROC(kb_proc)
    cb_ms = HOOKPROC(ms_proc)

    hk_kb = u32.SetWindowsHookExW(
        WH_KEYBOARD_LL, cb_kb, None, 0
    )
    hk_ms = u32.SetWindowsHookExW(
        WH_MOUSE_LL, cb_ms, None, 0
    )

    _log("hooks installed: kb=%s ms=%s err=%d" % (
        hk_kb, hk_ms, ctypes.get_last_error()
    ))

    return cb_kb, cb_ms, hk_kb, hk_ms


def _hook_thread():
    k32.SetThreadPriority(k32.GetCurrentThread(), 15)

    refs = _make_hooks()
    msg = W.MSG()

    while u32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        u32.TranslateMessage(ctypes.byref(msg))
        u32.DispatchMessageW(ctypes.byref(msg))

    return refs


def _tick_once():
    if not S.active or not _spam_win_ok() or _chat_open():
        return

    for vk in tuple(_held):
        if vk in S.spam_vks and not _mods_blocked(vk):
            tap_key(vk)

    if S.spam_x1 and _held_x[1]:
        tap_xbtn(XBUTTON1)

    if S.spam_x2 and _held_x[2]:
        tap_xbtn(XBUTTON2)


def _spam_thread():
    k32.SetThreadPriority(k32.GetCurrentThread(), 2)

    timer = None

    try:
        timer = k32.CreateWaitableTimerExW(None, None, 0x2, 0x1F0003)
    except Exception:
        timer = None

    if not timer:
        timer = k32.CreateWaitableTimerW(None, True, None)

    waitables = (_vp * 2)(_wake, timer)
    pc = time.perf_counter
    next_tick = None

    while True:
        try:
            period = max(1, S.interval_ms) / 1000.0

            while True:
                try:
                    kind, which = _press_q.get_nowait()
                except queue.Empty:
                    break

                if kind == "k":
                    if which in _held:
                        tap_key(which)
                else:
                    if _held_x[which]:
                        tap_xbtn(XBUTTON1 if which == 1 else XBUTTON2)

            holding = bool(_held) or _held_x[1] or _held_x[2]
            now = pc()

            if not holding:
                next_tick = None
            elif next_tick is None or next_tick - now > period:
                next_tick = now + period

            if next_tick is not None and now >= next_tick:
                _tick_once()
                next_tick += period

                if pc() - next_tick > period:
                    next_tick = pc() + period

                continue

            if next_tick is None:
                if timer:
                    k32.CancelWaitableTimer(timer)

                k32.WaitForMultipleObjects(1, waitables, False, 0xFFFFFFFF)

            else:
                delta = next_tick - now

                if timer:
                    due = ctypes.c_longlong(-max(1, int(delta * 1e7)))
                    k32.SetWaitableTimer(
                        timer, ctypes.byref(due), 0, None, None, False
                    )
                    k32.WaitForMultipleObjects(
                        2, waitables, False, 0xFFFFFFFF
                    )
                else:
                    k32.WaitForMultipleObjects(
                        1, waitables, False,
                        max(0, int(math.ceil(delta * 1000)))
                    )

        except Exception:
            time.sleep(0.005)
