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
    PM_REMOVE,
    QS_ALLINPUT,
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

        # Fast exit: ignore everything except X-button messages
        if nCode >= 0 and (wParam == WM_XBUTTONDOWN or wParam == WM_XBUTTONUP):
            try:
                ms = ctypes.cast(
                    lParam, ctypes.POINTER(MSLLHOOKSTRUCT)
                ).contents

                if ms.dwExtraInfo != INJECTED:
                    which = (ms.mouseData >> 16) & 0xFFFF

                    if which in (1, 2):
                        want = S.spam_x1 if which == 1 else S.spam_x2

                        if wParam == WM_XBUTTONDOWN:
                            # A new physical press always restarts the cycle,
                            # even if a previous release was missed.
                            if want and S.active and _spam_win_ok() \
                                    and not _chat_open():
                                _held_x[which] = True
                                _press_q.put(("x", which))
                                k32.SetEvent(_wake)
                                return 1

                            _held_x[which] = False

                        elif _held_x[which]:
                            _held_x[which] = False
                            return 1

                        # release with no matching press: pass through

            except Exception:
                pass

        return u32.CallNextHookEx(None, nCode, wParam, lParam)

    return kb_proc, ms_proc


_HOOK_REFRESH_S = 20.0


def _hook_thread():
    k32.SetThreadPriority(k32.GetCurrentThread(), 15)

    kb_proc, ms_proc = _make_hooks()
    cb_kb = HOOKPROC(kb_proc)
    cb_ms = HOOKPROC(ms_proc)

    hk = {"kb": None, "ms": None}
    last_refresh = time.monotonic()

    def unhook(name):
        if hk[name]:
            u32.UnhookWindowsHookEx(hk[name])
            hk[name] = None

    def install(name):
        if hk[name]:
            return

        if name == "kb":
            hk[name] = u32.SetWindowsHookExW(WH_KEYBOARD_LL, cb_kb, None, 0)
        else:
            hk[name] = u32.SetWindowsHookExW(WH_MOUSE_LL, cb_ms, None, 0)

        _log("hook %s installed: %s err=%d" % (
            name, hk[name], ctypes.get_last_error()
        ))

    msg = W.MSG()

    while True:
        try:
            need_ms = bool(S.spam_x1 or S.spam_x2)
            idle = (
                not _held and not _held_raw
                and not _held_x[1] and not _held_x[2]
            )
            now = time.monotonic()

            # Windows silently drops slow hooks: reinstall when idle
            if idle and now - last_refresh >= _HOOK_REFRESH_S:
                unhook("kb")
                unhook("ms")
                last_refresh = now

            install("kb")

            # Only listen to the mouse while M4/M5 spam is enabled
            if need_ms:
                install("ms")
            else:
                unhook("ms")
                _held_x[1] = _held_x[2] = False

            while u32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
                u32.TranslateMessage(ctypes.byref(msg))
                u32.DispatchMessageW(ctypes.byref(msg))

            u32.MsgWaitForMultipleObjects(0, None, False, 250, QS_ALLINPUT)

        except Exception:
            time.sleep(0.05)


def _tick_once():
    if not S.active or not _spam_win_ok() or _chat_open():
        return

    for vk in tuple(_held):
        if vk in S.spam_vks and not _mods_blocked(vk):
            tap_key(vk)

    if not S.spam_x1:
        _held_x[1] = False

    if not S.spam_x2:
        _held_x[2] = False

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

                # Always send the first click, even if the button was
                # already released (quick tap): the real click was swallowed.
                if kind == "k":
                    tap_key(which)
                else:
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
