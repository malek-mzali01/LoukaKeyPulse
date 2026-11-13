# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import base64
import os
import time
import tkinter as tk

from .config import _log
from .imaging import _icon_png
from .state import S
from .theme import ACC, FT, HOV, KB, KT, PANEL, PANEL2, SEL, SUB
from .winutil import _list_apps


class TargetsMixin:
    def _tgt_text(self):
        t = sorted(S.targets)

        if not t:
            s = "Any window"
        elif len(t) == 1:
            s = os.path.splitext(t[0])[0]
        else:
            s = "%d apps" % len(t)

        return s + "  \u25be"

    def _icon(self, path):
        if path in self._icons:
            return self._icons[path]

        img = None

        if path:
            try:
                png = _icon_png(
                    path, 24, (0x23, 0x23, 0x2f)
                )

                if png:
                    img = tk.PhotoImage(
                        data=base64.b64encode(png).decode("ascii")
                    )

            except Exception as e:
                _log("icon error: %s" % e)

        if img is None:
            if self._blank is None:
                self._blank = tk.PhotoImage(width=24, height=24)
                self._blank.put(KB, to=(4, 4, 20, 20))

            img = self._blank

        self._icons[path] = img
        return img

    def _targets_open(self):
        lc = self._last_closed

        if lc[0] == "target" and time.time() - lc[1] < 0.3:
            return

        self._close_pop()

        pop = tk.Toplevel(self.root)
        pop.overrideredirect(True)
        pop.attributes("-topmost", True)
        pop.configure(bg=ACC)

        box = tk.Frame(pop, bg=PANEL)
        box.pack(padx=1, pady=1)

        hd = tk.Frame(box, bg=PANEL)
        hd.pack(fill="x", padx=10, pady=(8, 4))

        tk.Label(
            hd, text="Target applications",
            bg=PANEL, fg=KT, font=(FT, 10, "bold")
        ).pack(side="left")

        def mk(txt, cmd):
            l = tk.Label(
                hd, text=txt, bg=PANEL2, fg=KT,
                font=(FT, 9, "bold"), padx=8, pady=2,
                cursor="hand2"
            )

            l.bind("<Button-1>", lambda e: cmd())
            l.bind("<Enter>", lambda e: l.configure(bg=HOV))
            l.bind("<Leave>", lambda e: l.configure(bg=PANEL2))

            return l

        mk("\u21bb", self._tg_fill).pack(side="right")
        mk("Clear", self._tg_clear).pack(
            side="right", padx=(0, 6)
        )

        cv = tk.Canvas(
            box, bg=PANEL, highlightthickness=0,
            width=340, height=200, yscrollincrement=24
        )
        cv.pack(padx=4)

        inner = tk.Frame(cv, bg=PANEL)

        cv.create_window(
            0, 0, window=inner, anchor="nw", width=340
        )

        inner.bind(
            "<Configure>",
            lambda e: cv.configure(scrollregion=cv.bbox("all"))
        )

        cv.bind(
            "<MouseWheel>",
            lambda e: cv.yview_scroll(
                -1 if e.delta > 0 else 1, "units"
            )
        )

        self._tg_cv = cv
        self._tg_inner = inner

        tk.Label(
            box, text="nothing selected = any window",
            bg=PANEL, fg=SUB, font=(FT, 8)
        ).pack(anchor="w", padx=12, pady=(2, 8))

        self._pop = pop
        self._pop_t = time.time()
        self._pop_kind = "target"

        self._tg_fill()
        pop.update_idletasks()

        x = self.tgb.winfo_rootx()
        y = self.tgb.winfo_rooty() + self.tgb.winfo_height() + 6

        pop.geometry("+%d+%d" % (x, y))
        pop.bind("<Escape>", lambda e: self._close_pop())

    def _wheel(self, w):
        w.bind(
            "<MouseWheel>",
            lambda e: self._tg_cv.yview_scroll(
                -1 if e.delta > 0 else 1, "units"
            )
        )

        for c in w.winfo_children():
            self._wheel(c)

    def _tg_fill(self):
        inner = self._tg_inner

        for w in inner.winfo_children():
            w.destroy()

        apps = _list_apps()
        have = {a["exe"] for a in apps}

        apps += [
            dict(exe=e, path="", title="not running")
            for e in S.targets - have
        ]

        apps.sort(
            key=lambda a: (
                a["exe"] not in S.targets, a["exe"]
            )
        )

        for a in apps:
            self._tg_row(a)

        self._wheel(inner)
        inner.update_idletasks()

        self._tg_cv.configure(
            height=max(60, min(inner.winfo_reqheight(), 336))
        )

    def _tg_row(self, a):
        exe = a["exe"]

        row = tk.Frame(
            self._tg_inner, bg=PANEL2, cursor="hand2"
        )
        row.pack(fill="x", padx=4, pady=2)

        chk = tk.Label(
            row, width=2, font=(FT, 10, "bold"), fg="#fff"
        )
        chk.pack(side="left", padx=(8, 6), pady=8)

        ic = tk.Label(
            row, image=self._icon(a["path"]), bg=PANEL2
        )
        ic.pack(side="left", padx=(0, 8))

        tx = tk.Frame(row, bg=PANEL2)
        tx.pack(side="left", fill="x")

        nm = tk.Label(
            tx, text=os.path.splitext(exe)[0],
            bg=PANEL2, font=(FT, 10, "bold"), anchor="w"
        )
        nm.pack(anchor="w")

        t = a["title"]

        tt = tk.Label(
            tx,
            text=(t[:44] + "\u2026") if len(t) > 45 else t,
            bg=PANEL2, fg=SUB, font=(FT, 8), anchor="w"
        )
        tt.pack(anchor="w")

        def paint():
            on = exe in S.targets

            chk.configure(
                text="\u2713" if on else "",
                bg=ACC if on else KB
            )
            nm.configure(fg=SEL if on else KT)

        def toggle(e=None):
            if exe in S.targets:
                S.targets.discard(exe)
            else:
                S.targets.add(exe)

            paint()
            self.tgb.configure(text=self._tgt_text())
            self.save()

        paint()

        for w in (row, chk, ic, tx, nm, tt):
            w.bind("<Button-1>", toggle)

    def _tg_clear(self):
        S.targets.clear()
        self.tgb.configure(text=self._tgt_text())
        self.save()
        self._tg_fill()
