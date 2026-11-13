# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import threading
import time
import tkinter as tk

from .keymap import _LBLVK, _display_key_name, _rows, _vkn
from .state import S, _cap_event, _cap_result, _cap_state
from .theme import (
    ACC,
    BG,
    DB,
    DT,
    FT,
    G,
    HOV,
    KB,
    KH,
    KT,
    PANEL,
    PANEL2,
    RED,
    SEL,
    SELT,
    SUB,
    U,
    rr
)


class KeysMixin:
    def _dkb(self):
        c = self.kbc
        c.delete("all")
        self.kmap.clear()
        self._lit = set()

        rows = _rows(self.hkl)

        W2 = (
            max(sum(w for _, _, w in r) for r in rows) * U
            + max(len(r) for r in rows) * G
        )
        H2 = len(rows) * (KH + G) + G

        c.configure(width=W2 + 12, height=H2 + 12)

        y = G + 6
        ti = 0

        for row in rows:
            x = G + 6
            seen = {}

            for lbl, vk, wu in row:
                kw = wu * U + (wu - 1) * G
                sel = vk is not None
                tag = "k%d" % ti
                ti += 1

                on = sel and vk in S.spam_vks
                fill = SEL if on else KB if sel else DB

                rect = rr(
                    c, x, y, x + kw, y + KH, 6,
                    fill=fill, outline="", tags=(tag,)
                )

                tc = SELT if on else KT if sel else DT
                fs = 11 if len(lbl) <= 2 else 9

                txt = c.create_text(
                    x + kw / 2, y + KH / 2,
                    text=lbl, fill=tc,
                    font=(FT, fs, "bold"), tags=(tag,)
                )

                dot = None

                if sel:
                    dot = c.create_oval(
                        x + kw - 13, y + 5, x + kw - 6, y + 12,
                        fill=SELT, outline="", tags=(tag,),
                        state="normal" if (
                            on and S.blocked.get(vk)
                        ) else "hidden"
                    )

                if vk is not None:
                    pv = {vk}
                elif lbl in _LBLVK:
                    t = _LBLVK[lbl]
                    n = seen.get(lbl, 0)
                    seen[lbl] = n + 1
                    pv = {t[min(n, len(t) - 1)]}
                else:
                    pv = set()

                self.kmap[tag] = dict(
                    vk=vk, rect=rect, txt=txt,
                    sel=sel, dot=dot, pv=pv
                )

                if sel:
                    c.tag_bind(
                        tag, "<Button-1>",
                        lambda e, t=tag: self._tk(t)
                    )
                    c.tag_bind(
                        tag, "<Button-3>",
                        lambda e, t=tag: self._tk(t)
                    )
                    c.tag_bind(
                        tag, "<Enter>",
                        lambda e, t=tag: self._hov(t, True)
                    )
                    c.tag_bind(
                        tag, "<Leave>",
                        lambda e, t=tag: self._hov(t, False)
                    )

                x += kw + G

            y += KH + G

    def _rpk(self, tag):
        k = self.kmap[tag]
        s = k["vk"] in S.spam_vks

        self.kbc.itemconfig(k["rect"], fill=SEL if s else KB)
        self.kbc.itemconfig(k["txt"], fill=SELT if s else KT)

        if k.get("dot"):
            self.kbc.itemconfig(
                k["dot"],
                state="normal" if (
                    s and S.blocked.get(k["vk"])
                ) else "hidden"
            )

    def _tk(self, tag):
        vk = self.kmap[tag]["vk"]

        if vk not in S.spam_vks:
            S.spam_vks.add(vk)
            self._rpk(tag)
            self.save()

        self._popup(tag)

    def _rm(self, tag):
        vk = self.kmap[tag]["vk"]

        S.spam_vks.discard(vk)
        S.blocked.pop(vk, None)

        self._rpk(tag)
        self.save()
        self._close_pop()

    def _popup(self, tag):
        self._close_pop()

        vk = self.kmap[tag]["vk"]
        blocked = S.blocked.setdefault(vk, set())

        pop = tk.Toplevel(self.root)
        pop.overrideredirect(True)
        pop.attributes("-topmost", True)
        pop.configure(bg=ACC)

        box = tk.Frame(pop, bg=PANEL)
        box.pack(padx=1, pady=1)

        tk.Label(
            box, text="%s  •  spam with:" % _display_key_name(vk),
            bg=PANEL, fg=KT, font=(FT, 10, "bold")
        ).pack(anchor="w", padx=12, pady=(8, 2))

        def flip(m, v):
            if v.get():
                blocked.discard(m)
            else:
                blocked.add(m)

            self._rpk(tag)
            self.save()

        for m, lbl in (
            ("shift", "Shift"),
            ("ctrl", "Ctrl"),
            ("alt", "Alt")
        ):
            v = tk.BooleanVar(value=(m not in blocked))

            tk.Checkbutton(
                box, text="%s + %s" % (lbl, _display_key_name(vk)),
                variable=v,
                command=lambda m=m, v=v: flip(m, v),
                bg=PANEL, fg=KT, selectcolor=PANEL2,
                activebackground=HOV, activeforeground=KT,
                bd=0, highlightthickness=0,
                font=(FT, 10), anchor="w", padx=10
            ).pack(fill="x", padx=4)

        tk.Label(
            box, text="unchecked = normal press, no spam",
            bg=PANEL, fg=SUB, font=(FT, 8)
        ).pack(anchor="w", padx=12, pady=(2, 4))

        tk.Button(
            box, text="Remove key",
            command=lambda: self._rm(tag),
            bg=PANEL2, fg=RED,
            activebackground=HOV, activeforeground=RED,
            relief="flat", bd=0, font=(FT, 9, "bold"),
            cursor="hand2", pady=4
        ).pack(fill="x", padx=8, pady=(0, 8))

        pop.update_idletasks()

        w, h = pop.winfo_reqwidth(), pop.winfo_reqheight()
        x1, y1, x2, y2 = self.kbc.bbox(tag)

        sx = (
            self.kbc.winfo_rootx()
            + (x1 + x2) // 2 - w // 2
        )
        sy = self.kbc.winfo_rooty() + y1 - h - 6

        if sy < 0:
            sy = self.kbc.winfo_rooty() + y2 + 6

        pop.geometry("+%d+%d" % (max(0, sx), sy))
        pop.bind("<Escape>", lambda e: self._close_pop())

        self._pop = pop
        self._pop_t = time.time()
        self._pop_kind = "keys"

    def _hov(self, tag, on):
        if tag in self._lit:
            return

        k = self.kmap[tag]

        if k["vk"] in S.spam_vks:
            return

        self.kbc.itemconfig(k["rect"], fill=HOV if on else KB)

    def _dms(self):
        c = self.msc
        c.delete("all")

        rr(c, 30, 7, 120, 211, 42, fill=KB, outline="")
        c.create_line(75, 9, 75, 83, fill=BG, width=2)
        rr(c, 66, 28, 84, 62, 7, fill=PANEL2, outline="")

        self._m4 = rr(
            c, 15, 65, 34, 94, 8,
            fill=SEL if S.spam_x1 else KB,
            outline="",
            tags=("m4",)
        )

        c.create_text(
            59, 80, text="M4", fill=SUB,
            font=(FT, 9, "bold")
        )

        self._m5 = rr(
            c, 15, 101, 34, 130, 8,
            fill=SEL if S.spam_x2 else KB,
            outline="",
            tags=("m5",)
        )

        c.create_text(
            59, 115, text="M5", fill=SUB,
            font=(FT, 9, "bold")
        )

        c.create_text(
            75, 225, text="side buttons",
            fill=SUB, font=(FT, 8)
        )

        for t in ("m4", "m5"):
            b = 1 if t == "m4" else 2

            c.tag_bind(
                t, "<Button-1>",
                lambda e, x=b: self._tm(x)
            )
            c.tag_bind(
                t, "<Enter>",
                lambda e: c.configure(cursor="hand2")
            )
            c.tag_bind(
                t, "<Leave>",
                lambda e: c.configure(cursor="")
            )

    def _tm(self, w):
        if w == 1:
            S.spam_x1 = not S.spam_x1
            self.msc.itemconfig(
                self._m4, fill=SEL if S.spam_x1 else KB
            )
        else:
            S.spam_x2 = not S.spam_x2
            self.msc.itemconfig(
                self._m5, fill=SEL if S.spam_x2 else KB
            )

        self.save()

    def _start_cap(self):

        _cap_result[0] = None
        _cap_event.clear()
        _cap_state["flag"] = False

        self.pkb.configure(text="press key\u2026", bg=ACC)

        threading.Thread(
            target=self._cap_poll, daemon=True
        ).start()

    def _cap_poll(self):

        time.sleep(0.3)
        _cap_state["flag"] = True

        _cap_event.wait()

        vk = _cap_result[0]

        if vk is not None:
            self.root.after(
                0, lambda: self._cap_done(vk)
            )

    def _cap_done(self, vk):
        S.pause_vk = vk
        self.pkb.configure(text=_vkn(vk), bg=PANEL2)
        self.save()

    def _paint(self, tag, on):
        k = self.kmap[tag]

        if on:
            self.kbc.itemconfig(k["rect"], fill=ACC)
            self.kbc.itemconfig(k["txt"], fill="#fff")

        elif k["sel"]:
            self._rpk(tag)

        else:
            self.kbc.itemconfig(k["rect"], fill=DB)
            self.kbc.itemconfig(k["txt"], fill=DT)
