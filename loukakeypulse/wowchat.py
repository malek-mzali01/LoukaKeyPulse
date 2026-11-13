# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import ctypes
import ctypes.wintypes as W
import json
import os
import time
import winsound

from .config import _APP_DIR, _cfg_lock, _load, _save
from .keyinput import _press_enter
from .state import S
from .winapi import MBI, MODULEINFO, VSFFI, _vp, k32, psapi, u32, verdll
from .winutil import _fg_exe, _fg_is, _focus_window, _hwnd_pid, _pid_path


CHAT_OFFSETS = []

_chat_map = {}
_chat_ver = {}

_wow = {"pid": 0, "h": None, "base": 0, "size": 0, "ver": "", "id": ""}

_learn = {"on": False, "stop": False, "msg": "", "until": 0.0}


def _chat_export():
    return {
        i: {"version": _chat_ver.get(i, ""), "offsets": o}
        for i, o in _chat_map.items()
    }


def _chat_map_load():
    try:
        d = dict(_load().get("chat_map") or {})

        try:
            with open(
                os.path.join(_APP_DIR, "chatmap.json"), encoding="utf-8"
            ) as f:
                for k, v in json.load(f).items():
                    d.setdefault(k, v)
        except Exception:
            pass

        for k, v in d.items():
            if isinstance(v, dict):
                _chat_map[str(k)] = [int(x) for x in v.get("offsets", [])]
                _chat_ver[str(k)] = str(v.get("version", ""))
            else:
                _chat_map[str(k)] = [int(x) for x in v]

    except Exception:
        pass


def _chat_map_save():
    with _cfg_lock:
        cfg = _load()
        cfg["chat_map"] = _chat_export()
        _save(cfg)


def _chat_store(best):
    _chat_map[_wow["id"]] = [best]
    _chat_ver[_wow["id"]] = _wow["ver"]
    _chat_map_save()
    _chat_select()


def _file_version(path):
    try:
        n = verdll.GetFileVersionInfoSizeW(path, None)

        if not n:
            return ""

        buf = ctypes.create_string_buffer(n)

        if not verdll.GetFileVersionInfoW(path, 0, n, buf):
            return ""

        p = _vp()
        ln = W.UINT(0)

        if (
            not verdll.VerQueryValueW(
                buf, "\\", ctypes.byref(p), ctypes.byref(ln)
            )
            or not p.value
        ):
            return ""

        fi = ctypes.cast(p, ctypes.POINTER(VSFFI)).contents

        return "%d.%d.%d.%d" % (
            fi.dwFileVersionMS >> 16, fi.dwFileVersionMS & 0xFFFF,
            fi.dwFileVersionLS >> 16, fi.dwFileVersionLS & 0xFFFF
        )

    except Exception:
        return ""


def _rd_h(h, addr, size):
    buf = ctypes.create_string_buffer(size)
    n = ctypes.c_size_t(0)

    ok = k32.ReadProcessMemory(h, addr, buf, size, ctypes.byref(n))

    if ok and n.value == size:
        return int.from_bytes(buf.raw[:size], "little")

    return None


def _rd(addr, size):
    return _rd_h(_wow["h"], addr, size)


def _chat_raw():
    if not CHAT_OFFSETS or not _wow["h"]:
        return None

    try:
        addr = _wow["base"] + CHAT_OFFSETS[0]

        for o in CHAT_OFFSETS[1:]:
            ptr = _rd(addr, 4)

            if not ptr:
                return None

            addr = ptr + o

        return _rd(addr, 1)

    except Exception:
        return None


def _chat_open():
    if _learn["on"]:
        return True

    if not _wow["h"] or not _fg_is(_wow["pid"]):
        return False

    return bool(_chat_raw())


def _looks_like_wow(hwnd, exe):
    if exe.startswith("wow"):
        return True

    try:
        buf = ctypes.create_unicode_buffer(64)
        u32.GetClassNameW(hwnd, buf, 64)
        return buf.value.startswith("GxWindowClass")
    except Exception:
        return False


def _is_game(hwnd, exe):
    if not exe:
        return False

    if S.targets:
        return exe in S.targets

    return _looks_like_wow(hwnd, exe)


def _wow_detach():
    if _wow["h"]:
        k32.CloseHandle(_wow["h"])

    _wow.update(pid=0, h=None, base=0, size=0, ver="", id="")
    CHAT_OFFSETS[:] = []


def _proc_info(h, pid):
    mods = (_vp * 1)()
    need = W.DWORD(0)
    mi = MODULEINFO()

    if not (
        psapi.EnumProcessModulesEx(
            h, mods, ctypes.sizeof(mods), ctypes.byref(need), 3
        )
        and mods[0]
        and psapi.GetModuleInformation(
            h, mods[0], ctypes.byref(mi), ctypes.sizeof(mi)
        )
    ):
        return None

    base, size = int(mods[0]), int(mi.SizeOfImage)
    ver = _file_version(_pid_path(pid))

    nt = _rd_h(h, base + 0x3C, 4)
    ts = _rd_h(h, base + nt + 8, 4) if nt else None

    bid = (
        "%08X-%X" % (ts, size) if ts is not None
        else "%s-%X" % (ver or "x", size)
    )

    return base, size, ver, bid


def _wow_attach(pid):
    h = k32.OpenProcess(0x0410, False, pid)

    if not h:
        return

    info = _proc_info(h, pid)

    if info:
        base, size, ver, bid = info
        _wow.update(pid=pid, h=h, base=base, size=size, ver=ver, id=bid)
    else:
        k32.CloseHandle(h)


def _chat_select():
    offs = list(_chat_map.get(_wow["id"]) or [])

    if offs != CHAT_OFFSETS:
        CHAT_OFFSETS[:] = offs


def _proc_alive(h):
    code = W.DWORD(0)
    return bool(
        k32.GetExitCodeProcess(h, ctypes.byref(code))
    ) and code.value == 259


def _chat_watch():
    last_scan = 0.0

    while True:
        try:
            if _wow["h"] and not _proc_alive(_wow["h"]):
                _wow_detach()

            if time.time() - last_scan > 2.0 and not _learn["on"]:
                last_scan = time.time()
                _scan_targets()

            hwnd = u32.GetForegroundWindow()

            if hwnd and _is_game(hwnd, _fg_exe()):
                pid = _hwnd_pid(hwnd)

                if pid and pid != _wow["pid"]:
                    _wow_detach()
                    _wow_attach(pid)

            elif not _wow["h"] and _tstate:
                _wow_attach(_tstate[0]["pid"])

            if _wow["h"]:
                _chat_select()

        except Exception:
            pass

        time.sleep(0.5)


def _snap():
    size, base, h = _wow["size"], _wow["base"], _wow["h"]
    buf = bytearray(size)
    end = base + size
    addr = base
    mbi = MBI()

    while addr < end:
        if not k32.VirtualQueryEx(
            h, addr, ctypes.byref(mbi), ctypes.sizeof(mbi)
        ):
            break

        ba = mbi.BaseAddress or addr
        rs = mbi.RegionSize
        start = max(ba, addr)
        stop = min(ba + rs, end)

        if (
            mbi.State == 0x1000
            and not (mbi.Protect & 0x101)
            and stop > start
        ):
            tmp = ctypes.create_string_buffer(stop - start)
            n = ctypes.c_size_t(0)

            k32.ReadProcessMemory(
                h, start, tmp, stop - start, ctypes.byref(n)
            )

            if n.value:
                o = start - base
                buf[o:o + n.value] = tmp.raw[:n.value]

        if rs <= 0:
            break

        addr = ba + rs

    return bytes(buf)


def _beep(freq):
    try:
        winsound.Beep(freq, 80)
    except Exception:
        pass


def _note(msg):
    if not _learn["on"]:
        _learn.update(msg=msg, until=time.time() + 6)


def _learn_end(msg):
    _learn.update(on=False, msg=msg, until=time.time() + 8)


_tstate = []
_probe_cache = {}


def _is_cal(bid):
    return bid in _chat_map


def _short(exe):
    return os.path.splitext(exe)[0][:12]


def _cal_need():
    return any(t["id"] and not t["cal"] for t in _tstate)


def _scan_targets():
    found = {}
    me = os.getpid()
    EP = ctypes.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)

    def cb(h, _):
        try:
            if u32.IsWindowVisible(h) and u32.GetWindowTextLengthW(h):
                pid = _hwnd_pid(h)

                if pid and pid != me and pid not in found:
                    exe = os.path.basename(_pid_path(pid)).lower()

                    if _is_game(h, exe):
                        found[pid] = (exe, h)

        except Exception:
            pass

        return True

    u32.EnumWindows(EP(cb), 0)

    out = []

    for pid, (exe, h) in found.items():
        info = _probe_cache.get(pid)

        if info is None:
            hp = k32.OpenProcess(0x0410, False, pid)

            if hp:
                try:
                    r = _proc_info(hp, pid)
                finally:
                    k32.CloseHandle(hp)

                if r:
                    info = _probe_cache[pid] = (r[3], r[2])

        bid, ver = info if info else ("", "")

        out.append({
            "exe": exe, "pid": pid, "hwnd": h, "id": bid, "ver": ver,
            "cal": bool(bid) and _is_cal(bid)
        })

    for pid in list(_probe_cache):
        if pid not in found:
            _probe_cache.pop(pid, None)

    out.sort(key=lambda t: (
        0 if t["exe"].startswith("wow") else 1,
        t["pid"]
    ))
    _tstate[:] = out
    return out


def _autocal(force, target_id=None):
    st = _learn
    ts = _scan_targets()

    if not ts:
        return "calibration: no WoW window found (start the game, " \
               "or pick it in Target apps)"

    readable = [t for t in ts if t["id"]]

    if not readable:
        return "calibration: cannot read %s (run as administrator?)" % (
            _short(ts[0]["exe"])
        )

    todo = [t for t in readable if not t["cal"]]

    if target_id:
        pick = next((t for t in readable if t["id"] == target_id), None)

        if pick is None:
            return "calibration: that build is not running"

    elif force:
        pick = next(
            (t for t in readable if t["pid"] == _wow["pid"]), readable[0]
        )
    elif todo:
        pick = todo[0]
    else:
        return "calibration: all selected apps are already calibrated " \
               "(Shift+click to redo)"

    hwnd, pid, name = pick["hwnd"], pick["pid"], _short(pick["exe"])

    if pid != _wow["pid"] or not _wow["h"]:
        _wow_detach()
        _wow_attach(pid)

    if not _wow["h"]:
        return "calibration: cannot read %s (run as administrator?)" % name

    _chat_select()

    st["msg"] = "calibrating %s: focusing the window..." % name

    if not _focus_window(hwnd, pid):
        return "calibration: could not focus the game window"

    time.sleep(0.5)

    n_snaps = 11
    c1, c2 = {}, {}
    s0 = None

    for k in range(n_snaps):
        if st["stop"]:
            return "calibration cancelled"

        if not _fg_is(pid) and not _focus_window(hwnd, pid):
            return "calibration aborted: the game lost focus"

        if k:
            _press_enter()
            time.sleep(0.35)

        st["msg"] = "calibrating %s %d/%d - hands off the keyboard" % (
            name, k + 1, n_snaps
        )

        data = _snap()

        if k == 0:
            s0 = data
            continue

        if k == 1:
            ch = 512

            for kk in range(0, len(s0), ch):
                if s0[kk:kk + ch] != data[kk:kk + ch]:
                    for i in range(kk, min(kk + ch, len(s0))):
                        a, b = s0[i], data[i]

                        if a == 0 and b != 0:
                            c1[i] = b
                        elif a != 0 and b == 0:
                            c2[i] = a

            s0 = None

        else:
            even = k % 2 == 0
            c1 = {
                i: v for i, v in c1.items() if (data[i] == 0) == even
            }
            c2 = {
                i: v for i, v in c2.items() if (data[i] != 0) == even
            }

        if not c1 and not c2:
            return "calibration failed: nothing reacts to the chat box " \
                   "(be in the world, not at the login screen)"

    pool = c1 or c2

    if len(pool) > 500:
        return "calibration failed: too noisy (%d candidates), try again" \
               % len(pool)

    best = sorted(
        pool.items(), key=lambda kv: (kv[1] != 1, kv[0])
    )[0][0]

    _chat_store(best)
    _beep(1200)

    left = [t for t in _scan_targets() if t["id"] and not t["cal"]]

    return "calibrated %s: Wow.exe+0x%X (%d candidates), build %s%s" % (
        name, best, len(pool), _wow["ver"] or _wow["id"],
        (" - NOT calibrated yet: %s (click again)" %
         ", ".join(_short(t["exe"]) for t in left)) if left else ""
    )


def _autocal_thread(force, target_id=None):
    _learn.update(
        on=True, stop=False, until=0.0, msg="calibrating: looking for the game..."
    )

    try:
        msg = _autocal(force, target_id)
    except Exception as e:
        msg = "calibration failed: %s" % e

    _learn_end(msg)
