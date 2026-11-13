# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import json
import os
import time
import tkinter as tk
from tkinter import filedialog

from .config import _pclean
from .state import _held
from .theme import ACC, FT, HOV, KB, KT, PANEL, PANEL2, RED, SEL, SUB
from .wowchat import _note


class ProfilesMixin:
    def _prof_text(self):
        n = self.active
        return (
            n if len(n) <= 16 else n[:15] + "\u2026"
        ) + "  \u25be"

    def _switch(self, name):
        if name == self.active or name not in self.profiles:
            return

        self.save()
        self.active = name
        self._pload(self.profiles[name])
        _held.clear()

        self._refresh_all()
        self.save()

    def _switch_close(self, name):
        self._switch(name)
        self._close_pop()

    def _pf_add(self, ent):
        n = ent.get().strip()[:20]

        if not n:
            return

        if n.lower() in {p.lower() for p in self.profiles}:
            self._pf_msg.configure(
                text="that name already exists", fg=RED
            )
            return

        self.profiles[n] = {}
        self._switch(n)
        self._close_pop()

    def _pf_del(self, n):
        self.profiles.pop(n, None)

        if n == self.active:
            self.active = "Default"
            self._pload(self.profiles["Default"])
            _held.clear()
            self._refresh_all()

        self.save()
        self._pf_fill()

    def _pf_fill(self):
        if not self._pop or self._pop_kind != "profile":
            return

        lst = self._pf_list

        for w in lst.winfo_children():
            w.destroy()

        tk.Frame(
            lst, bg=PANEL, width=270, height=0
        ).pack()

        for name in list(self.profiles):
            on = name == self.active

            row = tk.Frame(
                lst, bg=PANEL2, cursor="hand2"
            )
            row.pack(fill="x", padx=4, pady=2)

            chk = tk.Label(
                row, text="\u2713" if on else "", width=2,
                bg=ACC if on else KB, fg="#fff",
                font=(FT, 10, "bold")
            )
            chk.pack(side="left", padx=(8, 8), pady=8)

            nm = tk.Label(
                row, text=name, bg=PANEL2,
                fg=SEL if on else KT,
                font=(FT, 10, "bold"), anchor="w"
            )
            nm.pack(side="left", fill="x", expand=True)

            if name != "Default":
                dl = tk.Label(
                    row, text="\u2715", bg=PANEL2, fg=SUB,
                    font=(FT, 10, "bold"), padx=10, cursor="hand2"
                )
                dl.pack(side="right")

                st = {"arm": False}

                def kill(e, n=name, dl=dl, st=st):
                    if not st["arm"]:
                        st["arm"] = True
                        dl.configure(text="delete?", fg=RED)
                    else:
                        self._pf_del(n)

                    return "break"

                dl.bind("<Button-1>", kill)

            for w in (row, chk, nm):
                w.bind(
                    "<Button-1>",
                    lambda e, n=name: self._switch_close(n)
                )

    def _uniq_name(self, n):
        n = (n.strip()[:20]) or "Imported"
        taken = {p.lower() for p in self.profiles}
        base, i = n, 2

        while n.lower() in taken:
            suffix = " %d" % i
            n = base[:20 - len(suffix)] + suffix
            i += 1

        return n

    def _pf_export(self):
        self._close_pop()

        path = filedialog.asksaveasfilename(
            parent=self.root, title="Export profile",
            defaultextension=".json", initialfile=self.active + ".json",
            filetypes=[("LoukaKeyPulse profile", "*.json")]
        )

        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({
                    "loukakeypulse_profile": 1,
                    "name": self.active,
                    "data": self._pdata()
                }, f, indent=2)

            _note("exported profile '%s'" % self.active)

        except Exception as e:
            _note("export failed: %s" % e)

    def _pf_import(self):
        self._close_pop()

        path = filedialog.askopenfilename(
            parent=self.root, title="Import profile",
            filetypes=[
                ("LoukaKeyPulse profile", "*.json"), ("All files", "*.*")
            ]
        )

        if not path:
            return

        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)

            stem = os.path.splitext(os.path.basename(path))[0]

            if isinstance(raw.get("profiles"), dict):
                items = list(raw["profiles"].items())
            elif isinstance(raw.get("data"), dict):
                items = [(raw.get("name") or stem, raw["data"])]
            else:
                items = [(stem, raw)]

            last = None

            for name, d in items:
                clean = _pclean(d)
                n = self._uniq_name(str(name))
                self.profiles[n] = clean
                last = n

            if last:
                self._switch(last)

            _note("imported %d profile(s)" % len(items))

        except Exception as e:
            _note("import failed: %s" % e)

    def _prof_open(self):
        lc = self._last_closed

        if lc[0] == "profile" and time.time() - lc[1] < 0.3:
            return

        self._close_pop()

        pop = tk.Toplevel(self.root)
        pop.overrideredirect(True)
        pop.attributes("-topmost", True)
        pop.configure(bg=ACC)

        box = tk.Frame(pop, bg=PANEL)
        box.pack(padx=1, pady=1)

        tk.Label(
            box, text="Profiles", bg=PANEL, fg=KT,
            font=(FT, 10, "bold")
        ).pack(anchor="w", padx=12, pady=(8, 4))

        self._pf_list = tk.Frame(box, bg=PANEL)
        self._pf_list.pack(fill="x", padx=4)

        io = tk.Frame(box, bg=PANEL)
        io.pack(fill="x", padx=10, pady=(8, 0))

        def mk_io(txt, cmd):
            l = tk.Label(
                io, text=txt, bg=PANEL2, fg=KT, font=(FT, 9, "bold"),
                padx=12, pady=6, cursor="hand2"
            )
            l.pack(side="left", padx=(0, 6))
            l.bind("<Button-1>", lambda e: cmd())
            l.bind("<Enter>", lambda e: l.configure(bg=HOV))
            l.bind("<Leave>", lambda e: l.configure(bg=PANEL2))

        mk_io("\u2191 Export", self._pf_export)
        mk_io("\u2193 Import", self._pf_import)

        ar = tk.Frame(box, bg=PANEL)
        ar.pack(fill="x", padx=10, pady=(8, 2))

        ent = tk.Entry(
            ar, bg=PANEL2, fg=KT, insertbackground=KT,
            relief="flat", bd=0, font=(FT, 10),
            highlightthickness=1, highlightbackground=KB,
            highlightcolor=ACC
        )
        ent.pack(
            side="left", fill="x", expand=True, ipady=6
        )

        add = tk.Label(
            ar, text="+ Add", bg=ACC, fg="#fff",
            font=(FT, 9, "bold"), padx=12, pady=6,
            cursor="hand2"
        )
        add.pack(side="left", padx=(6, 0))

        add.bind(
            "<Button-1>", lambda e: self._pf_add(ent)
        )
        ent.bind("<Return>", lambda e: self._pf_add(ent))

        self._pf_msg = tk.Label(
            box, text="new profiles start empty",
            bg=PANEL, fg=SUB, font=(FT, 8)
        )
        self._pf_msg.pack(
            anchor="w", padx=12, pady=(2, 8)
        )

        self._pop = pop
        self._pop_t = time.time()
        self._pop_kind = "profile"

        self._pf_fill()
        pop.update_idletasks()

        x = self.prb.winfo_rootx()
        y = self.prb.winfo_rooty() + self.prb.winfo_height() + 6

        pop.geometry("+%d+%d" % (x, y))
        pop.bind("<Escape>", lambda e: self._close_pop())
        pop.after(60, ent.focus_force)
