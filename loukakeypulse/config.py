# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import json
import os
import shutil
import sys
import threading


if getattr(sys, "frozen", False):
    _BASE = os.path.dirname(sys.executable)
else:
    try:
        _BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    except Exception:
        _BASE = os.getcwd()


def _res(n):
    return os.path.join(getattr(sys, "_MEIPASS", _BASE), n)


APP_NAME = "LoukaKeyPulse"

_APPDATA = os.environ.get("APPDATA") or os.path.join(
    os.path.expanduser("~"), "AppData", "Roaming"
)

_APP_DIR = os.path.join(_APPDATA, APP_NAME)
CFG = os.path.join(_APP_DIR, "loukakeypulse.json")
LEGACY_CFG = os.path.join(_BASE, "loukaspammy.json")


def _log(msg):
    pass


_OLD_DIR = os.path.join(_APPDATA, "LoukaSpammy")


def _migrate_old():
    if os.path.isfile(CFG):
        return

    for old, new in (
        ("loukaspammy.json", "loukakeypulse.json"),
        ("chatmap.json", "chatmap.json")
    ):
        path = os.path.join(_OLD_DIR, old)

        if os.path.isfile(path):
            try:
                os.makedirs(_APP_DIR, exist_ok=True)
                shutil.copyfile(path, os.path.join(_APP_DIR, new))
            except Exception as e:
                _log("migration error: %s" % e)


def _load():
    try:
        os.makedirs(_APP_DIR, exist_ok=True)
        _migrate_old()

        if os.path.isfile(CFG):
            with open(CFG, encoding="utf-8") as f:
                return json.load(f)

        if os.path.isfile(LEGACY_CFG):
            with open(LEGACY_CFG, encoding="utf-8") as f:
                data = json.load(f)

            _save(data)
            return data

    except Exception as e:
        _log("config load error: %s" % e)

    return {}


_cfg_lock = threading.RLock()


def _save(data):
    with _cfg_lock:
        _save_raw(data)


def _save_raw(data):
    try:
        os.makedirs(_APP_DIR, exist_ok=True)

        temp_file = CFG + ".tmp"

        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        os.replace(temp_file, CFG)

    except Exception as e:
        _log("config save error: %s" % e)


def _pclean(d):
    return {
        "interval_ms": max(1, min(5000, int(d.get("interval_ms", 150)))),
        "targets": sorted({str(x).lower() for x in d.get("targets", [])}),
        "pause_vk": int(d.get("pause_vk", 0x7B)),
        "keys": sorted({int(x) for x in d.get("keys", [])}),
        "m4": bool(d.get("m4", False)),
        "m5": bool(d.get("m5", False)),
        "blocked": {
            str(int(k)): sorted(
                str(m) for m in v if m in ("shift", "ctrl", "alt")
            )
            for k, v in d.get("blocked", {}).items() if v
        }
    }


def updates_get():
    return dict(_load().get("updates") or {})


def updates_set(**kw):
    with _cfg_lock:
        cfg = _load()
        cur = dict(cfg.get("updates") or {})
        cur.update(kw)
        cfg["updates"] = cur
        _save(cfg)
