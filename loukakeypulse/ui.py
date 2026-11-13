# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import base64
import queue
import time
import tkinter as tk
import webbrowser

from . import __version__
from .config import APP_NAME, _cfg_lock, _load, _log, _res, _save
from .imaging import _icon_png
from .keyinput import _foreground_hkl
from .keymap import _vkn
from .state import S, _held_raw, _lock
from .theme import (
    ACC,
    BG,
    BORDER,
    DT,
    FH,
    FT,
    GRN,
    HOV,
    KT,
    P,
    PANEL,
    PANEL2,
    RED,
    SEL,
    SELT,
    SUB
)
from .tray import _tray_q, _tray_remove
from .ui_calibration import CalibrationMixin
from .ui_keys import KeysMixin
from .ui_profiles import ProfilesMixin
from .ui_targets import TargetsMixin
from .ui_update import UpdateMixin
from .winapi import SWP_NOSIZE, SW_MIN, u32
from .winutil import _fg_exe, _fg_title, _remove_titlebar, _win_ok
from .wowchat import (
    CHAT_OFFSETS,
    _cal_need,
    _chat_export,
    _chat_map,
    _chat_raw,
    _learn,
    _short,
    _tstate,
    _wow
)


class App(
    KeysMixin, ProfilesMixin, TargetsMixin, CalibrationMixin, UpdateMixin
):
    def __init__(self, root):
        self.root = root
        self.kmap = {}
        self._lit = set()

        cfg = _load()
        profs = cfg.get("profiles")

        if not isinstance(profs, dict) or not profs:
            profs = {
                "Default": {
                    k: cfg[k] for k in (
                        "interval_ms", "pause_vk", "keys",
                        "m4", "m5", "blocked", "targets"
                    ) if k in cfg
                }
            }

        if "Default" not in profs:
            profs = dict([("Default", {})] + list(profs.items()))

        self.profiles = profs
        self.active = (
            cfg.get("active")
            if cfg.get("active") in profs else "Default"
        )

        self._pload(profs[self.active])

        self._pop = None
        self._pop_t = 0
        self._pop_kind = None
        self._last_closed = ("", 0)
        self._icons = {}
        self._blank = None

        self.hkl = _foreground_hkl()
        self._layout_check_at = 0.0

        root.title(APP_NAME)

        try:
            root.iconbitmap(_res("icon.ico"))
        except Exception:
            pass

        root.configure(bg=BORDER)
        root.geometry("+80+80")
        root.resizable(False, False)
        root.bind("<Button-1>", self._root_click, add="+")
        root.protocol("WM_DELETE_WINDOW", self._hide_to_tray)
        self._poll_tray()

        self.body = tk.Frame(root, bg=BG)
        self.body.pack(fill="both", expand=False, padx=1, pady=1)

        self._hdr()
        self._ctrl()
        self._main()

        sb = tk.Frame(self.body, bg="#0e0e15")
        sb.pack(fill="x", side="bottom")

        self.stlbl = tk.Label(
            sb, text="", bg="#0e0e15", fg=SUB,
            anchor="w", font=(FT, 9), padx=12, pady=5
        )
        self.stlbl.pack(side="left", fill="x", expand=True)

        gh = tk.Label(
            sb, text="v%s  \u2022  by Louka" % __version__, bg="#0e0e15", fg=ACC,
            font=(FT, 9, "underline"), cursor="hand2", padx=12, pady=5
        )
        gh.pack(side="right")

        gh.bind(
            "<Button-1>",
            lambda e: webbrowser.open("https://github.com/Malek-Mzali")
        )
        gh.bind("<Enter>", lambda e: gh.configure(fg="#a08fff"))
        gh.bind("<Leave>", lambda e: gh.configure(fg=ACC))

        root.update_idletasks()
        root.after(50, self._strip_titlebar)

        self._tick()
        self._live()
        self._upd_init()

    def _strip_titlebar(self):
        try:
            hwnd = u32.GetParent(self.root.winfo_id())

            if not hwnd:
                hwnd = self.root.winfo_id()

            _remove_titlebar(hwnd)
            self._hwnd = hwnd
            self.root.after(60, self._fit)

        except Exception as e:
            _log("strip_titlebar error: %s" % e)

    def _fit(self):
        self.root.update_idletasks()
        w = self.body.winfo_reqwidth() + 2
        h = self.body.winfo_reqheight() + 2
        self.root.geometry("%dx%d" % (w, h))

    def _sd(self, e):
        self._ox = e.x_root - self.root.winfo_x()
        self._oy = e.y_root - self.root.winfo_y()

    def _dm(self, e):
        x = e.x_root - self._ox
        y = e.y_root - self._oy

        try:
            hwnd = getattr(
                self, "_hwnd", None
            ) or u32.GetParent(self.root.winfo_id())

            if hwnd:
                SWP_NOZORDER = 0x0004
                SWP_NOACTIVATE = 0x0010

                u32.SetWindowPos(
                    hwnd, None, x, y, 0, 0,
                    SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE
                )
                return

        except Exception:
            pass

        self.root.geometry("+%d+%d" % (x, y))

    def _btn(self, p, txt, cmd, bg=PANEL2, fg=KT, w=None):
        b = tk.Button(
            p, text=txt, command=cmd, bg=bg, fg=fg,
            activebackground=HOV, activeforeground=KT,
            relief="flat", bd=0, font=(FT, 10, "bold"),
            padx=14, pady=8, cursor="hand2"
        )

        if w:
            b.configure(width=w)

        return b

    def _hdr(self):
        h = tk.Frame(self.body, bg=BG)
        h.pack(fill="x", padx=P, pady=(12, 6))

        logo = None

        try:
            png = _icon_png(_res("icon.ico"), 32, (0x13, 0x13, 0x1c))

            if png:
                logo = tk.PhotoImage(
                    data=base64.b64encode(png).decode("ascii")
                )

        except Exception:
            logo = None

        if logo:
            self._logo = logo
            ti = tk.Label(
                h, image=logo, text="  " + APP_NAME,
                compound="left", bg=BG, fg="#fff",
                font=(FT, 16, "bold")
            )
        else:
            ti = tk.Label(
                h, text="\u26a1 " + APP_NAME,
                bg=BG, fg="#fff", font=(FT, 16, "bold")
            )

        ti.pack(side="left")

        xb = tk.Label(
            h, text="\u2715", bg=BG, fg=SUB,
            font=(FT, 13, "bold"), cursor="hand2", padx=8
        )
        xb.pack(side="right")
        xb.bind("<Button-1>", lambda e: self._hide_to_tray())
        xb.bind("<Enter>", lambda e: xb.configure(fg=RED))
        xb.bind("<Leave>", lambda e: xb.configure(fg=SUB))

        mb = tk.Label(
            h, text="\u2013", bg=BG, fg=SUB,
            font=(FT, 14, "bold"), cursor="hand2", padx=8
        )
        mb.pack(side="right")

        mb.bind(
            "<Button-1>",
            lambda e: u32.ShowWindow(
                u32.GetParent(self.root.winfo_id()), SW_MIN
            )
        )
        mb.bind("<Enter>", lambda e: mb.configure(fg=KT))
        mb.bind("<Leave>", lambda e: mb.configure(fg=SUB))

        for w in (h, ti):
            w.bind("<Button-1>", self._sd)
            w.bind("<B1-Motion>", self._dm)

    def _field(self, parent, col, caption, w, weight=0):
        f = tk.Frame(parent, bg=PANEL)
        f.grid(
            row=0, column=col, sticky="nsew",
            padx=(0 if col == 0 else 10, 0)
        )

        parent.columnconfigure(col, weight=weight, minsize=w)

        cr = tk.Frame(f, bg=PANEL)
        cr.pack(fill="x")

        tk.Label(
            cr, text=caption, bg=PANEL, fg=SUB,
            font=(FT, 9), anchor="w"
        ).pack(side="left")

        box = tk.Frame(f, bg=PANEL2, height=FH, width=w)
        box.pack(fill="x", pady=(4, 0))
        box.pack_propagate(False)

        return cr, box

    def _cbtn(self, box, txt, cmd, bg=PANEL2, fg=KT):
        b = tk.Button(
            box, text=txt, command=cmd, bg=bg, fg=fg,
            activebackground=HOV, activeforeground=KT,
            relief="flat", bd=0, font=(FT, 10, "bold"),
            cursor="hand2"
        )
        b.pack(fill="both", expand=True)
        return b

    def _ctrl(self):
        bar = tk.Frame(self.body, bg=PANEL)
        bar.pack(fill="x", padx=P, pady=4)

        inn = tk.Frame(bar, bg=PANEL)
        inn.pack(fill="x", padx=12, pady=12)

        _, b = self._field(inn, 0, "Auto-fire", 110)
        self.enb = self._cbtn(
            b, "DISABLED", self._tog, bg=RED, fg="#fff"
        )

        cr, b = self._field(inn, 1, "Interval", 170, 1)
        self.ivl = tk.Label(
            cr, text="", bg=PANEL, fg=KT, font=(FT, 9, "bold")
        )
        self.ivl.pack(side="right")
        self.ivl.configure(cursor="xterm")
        self.ivl.bind("<Button-1>", self._ivl_edit)
        self.ivl.bind("<Enter>", lambda e: self.ivl.configure(fg=ACC))
        self.ivl.bind("<Leave>", lambda e: self.ivl.configure(fg=KT))

        self.ivc = tk.Canvas(
            b, bg=PANEL2, highlightthickness=0,
            height=FH, cursor="hand2"
        )
        self.ivc.pack(fill="both", expand=True)
        self.ivc.bind("<Configure>", lambda e: self._ivl_draw())
        self.ivc.bind("<Button-1>", self._ivl_ev)
        self.ivc.bind("<B1-Motion>", self._ivl_ev)
        self.ivc.bind("<ButtonRelease-1>", lambda e: self.save())

        _, b = self._field(inn, 2, "Target apps", 160, 1)
        self.tgb = self._cbtn(
            b, self._tgt_text(), self._targets_open
        )

        _, b = self._field(inn, 3, "Profile", 150, 1)
        self.prb = self._cbtn(
            b, self._prof_text(), self._prof_open
        )

        _, b = self._field(inn, 4, "Toggle key", 100)
        self.pkb = self._cbtn(
            b, _vkn(S.pause_vk), self._start_cap
        )

        _, b = self._field(inn, 5, "Chat flag", 160)
        self.mnb = tk.Button(
            b, text="\u2630", command=self._man_open, bg=PANEL2, fg=KT,
            activebackground=HOV, activeforeground=KT,
            disabledforeground=DT, relief="flat", bd=0,
            font=(FT, 12, "bold"), cursor="hand2", width=3,
            state="normal" if _chat_map else "disabled"
        )
        self.mnb.pack(side="right", fill="y")
        tk.Frame(b, bg=PANEL, width=2).pack(side="right", fill="y")
        self.calb = self._cbtn(b, self._cal_text(), self._cal_click)
        self._cal_shift = False
        self.calb.bind(
            "<ButtonPress-1>",
            lambda e: setattr(self, "_cal_shift", bool(e.state & 0x1)),
            add="+"
        )

    def _main(self):
        m = tk.Frame(self.body, bg=BG)
        m.pack(padx=P, pady=(4, 8), anchor="w")

        self.kbc = tk.Canvas(m, bg=BG, highlightthickness=0)
        self.kbc.pack(side="left", anchor="n")

        self._dkb()

        r = tk.Frame(m, bg=BG)
        r.pack(side="left", anchor="n", padx=(16, 0))

        self.msc = tk.Canvas(
            r, bg=BG, width=170, height=238,
            highlightthickness=0
        )
        self.msc.pack(anchor="nw")
        self._dms()

    def _close_pop(self):
        if self._pop:
            try:
                self._pop.destroy()
            except Exception:
                pass

            self._last_closed = (self._pop_kind, time.time())
            self._pop = None

    def _root_click(self, e):
        if self._pop and time.time() - self._pop_t > 0.2:
            self._close_pop()

    def _tog(self):
        with _lock:
            S.active = not S.active

    def _ivl_draw(self):
        c = self.ivc
        c.delete("all")

        w = max(c.winfo_width(), 80)
        cy = FH // 2
        lo = 14
        hi = w - 14

        x = lo + min(1.0, (S.interval_ms - 1) / 499.0) * (hi - lo)

        c.create_line(
            lo, cy, hi, cy, width=6,
            capstyle="round", fill="#4a4a66"
        )

        if x > lo:
            c.create_line(
                lo, cy, x, cy, width=6,
                capstyle="round", fill=ACC
            )

        c.create_oval(
            x - 8, cy - 8, x + 8, cy + 8,
            fill="#ffffff", outline=ACC, width=3
        )

        self.ivl.configure(text="%d ms" % S.interval_ms)

    def _ivl_ev(self, e):
        w = max(self.ivc.winfo_width(), 80)
        lo = 14
        hi = w - 14

        f = min(1.0, max(0.0, (e.x - lo) / float(hi - lo)))
        S.interval_ms = int(round(1 + f * 499))

        self._ivl_draw()

    def _ivl_edit(self, e=None):
        if getattr(self, "_ive", None):
            return

        ent = tk.Entry(
            self.ivl.master, width=5, justify="right", bg=PANEL2, fg=KT,
            insertbackground=KT, relief="flat", bd=0,
            font=(FT, 9, "bold"), highlightthickness=1,
            highlightbackground=ACC, highlightcolor=ACC
        )
        ent.insert(0, str(S.interval_ms))
        ent.select_range(0, "end")

        self.ivl.pack_forget()
        ent.pack(side="right")
        ent.focus_force()
        self._ive = ent

        def done(apply):
            if self._ive is None:
                return

            self._ive = None

            if apply:
                try:
                    S.interval_ms = max(1, min(5000, int(ent.get().strip())))
                except ValueError:
                    pass

            ent.destroy()
            self.ivl.pack(side="right")
            self._ivl_draw()
            self.save()

        ent.bind("<Return>", lambda e: done(True))
        ent.bind("<KP_Enter>", lambda e: done(True))
        ent.bind("<Escape>", lambda e: done(False))
        ent.bind("<FocusOut>", lambda e: done(True))

    def _pdata(self):
        return {
            "interval_ms": S.interval_ms,
            "targets": sorted(S.targets),
            "pause_vk": S.pause_vk,
            "keys": sorted(S.spam_vks),
            "m4": S.spam_x1,
            "m5": S.spam_x2,
            "blocked": {
                str(k): sorted(v)
                for k, v in S.blocked.items() if v
            }
        }

    def _pload(self, d):
        S.interval_ms = max(
            1, min(5000, int(d.get("interval_ms", 150)))
        )

        S.targets = {
            str(x).lower() for x in d.get("targets", [])
        }

        S.pause_vk = int(d.get("pause_vk", 0x7B))
        S.spam_vks = set(d.get("keys", []))
        S.spam_x1 = bool(d.get("m4", False))
        S.spam_x2 = bool(d.get("m5", False))

        S.blocked = {
            int(k): set(v)
            for k, v in d.get("blocked", {}).items() if v
        }

    def _refresh_all(self):
        self._dkb()
        self._dms()
        self._ivl_draw()

        self.tgb.configure(text=self._tgt_text())
        self.pkb.configure(text=_vkn(S.pause_vk), bg=PANEL2)
        self.prb.configure(text=self._prof_text())

    def save(self):
        self.profiles[self.active] = self._pdata()

        with _cfg_lock:
            cfg = _load()
            cfg.update({
                "active": self.active,
                "profiles": self.profiles,
                "chat_map": _chat_export()
            })
            _save(cfg)

    def _hide_to_tray(self):
        self.save()
        self._close_pop()
        self.root.withdraw()

    def _show_from_tray(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.root.after(30, self._strip_titlebar)

    def _poll_tray(self):
        try:
            while True:
                c = _tray_q.get_nowait()

                if c == "quit":
                    self._quit()
                    return

                if c == "show":
                    self._show_from_tray()

                if c == "update":
                    self._upd_start(True)

        except queue.Empty:
            pass

        self.root.after(100, self._poll_tray)

    def _quit(self):
        self.save()
        _tray_remove()
        self.root.destroy()

    def _live(self):
        try:
            now = time.monotonic()

            if now >= self._layout_check_at:
                self._layout_check_at = now + 0.25

                active_hkl = _foreground_hkl()

                if active_hkl and active_hkl != self.hkl:
                    self.hkl = active_hkl
                    self._dkb()

            keys = set(_held_raw)

            lit = {
                t for t, k in self.kmap.items()
                if k["pv"] & keys
            }

            if lit != self._lit:
                for t in lit - self._lit:
                    self._paint(t, True)

                for t in self._lit - lit:
                    self._paint(t, False)

                self._lit = lit

        except Exception:
            pass

        self.root.after(50, self._live)

    def _check_pop(self):
        if not self._pop or time.time() - self._pop_t < 0.3:
            return

        try:
            m = 0xFFFFFFFF
            fg = u32.GetForegroundWindow() & m

            ids = (
                self.root.winfo_id(),
                self._pop.winfo_id()
            )

            ok = {getattr(self, "_hwnd", 0) & m}

            for i in ids:
                ok.add(i & m)
                ok.add(u32.GetParent(i) & m)

            if fg not in ok:
                self._close_pop()

        except Exception:
            self._close_pop()

    def _tick(self):
        self._check_pop()

        with _lock:
            act = S.active

        self.enb.configure(
            text="ENABLED" if act else "DISABLED",
            bg=GRN if act else RED
        )
        need = _cal_need() and not _learn["on"]
        self.calb.configure(
            text=self._cal_text(),
            bg=ACC if _learn["on"] else SEL if need else PANEL2,
            fg=SELT if need else "#fff" if _learn["on"] else KT
        )
        self.mnb.configure(state="normal" if _chat_map else "disabled")

        fg = (_fg_exe() or _fg_title())[:40]
        ok = "\u2713 match" if _win_ok() else "\u2717 no match"

        if _learn["on"] or time.time() < _learn["until"]:
            ok = _learn["msg"]

        elif CHAT_OFFSETS:
            raw = _chat_raw()
            ok += "  \u2022  chat flag: %s" % (
                "not attached" if raw is None else raw
            )

            if raw:
                ok = "chat open \u2013 paused  \u2022  chat flag: %s" % raw

        elif _wow["h"]:
            ok += (
                "  \u2022  chat: unknown build %s \u2013 "
                "click Chat flag > Calibrate" % (_wow["ver"] or _wow["id"])
            )

        if not _learn["on"] and (len(_tstate) > 1 or _cal_need()):
            ok += "  \u2022  chat: " + ", ".join(
                "%s %s" % (
                    _short(t["exe"]),
                    "\u2713" if t["cal"] else "\u2717" if t["id"] else "?"
                )
                for t in _tstate
            )

        self.stlbl.configure(
            text="state: %s  \u2022  focused: %r  (%s)" % (
                "ON" if act else "off", fg, ok
            )
        )

        self.root.after(250, self._tick)
