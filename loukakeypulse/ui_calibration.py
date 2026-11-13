# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import threading
import time
import tkinter as tk

from .theme import ACC, DT, FT, GRN, HOV, KB, KT, PANEL, PANEL2, RED, SUB
from .wowchat import (
    CHAT_OFFSETS,
    _autocal_thread,
    _cal_need,
    _chat_map,
    _chat_map_save,
    _chat_select,
    _chat_ver,
    _is_cal,
    _learn,
    _tstate,
    _wow
)


class CalibrationMixin:
    def _man_open(self):
        lc = self._last_closed

        if lc[0] == "manage" and time.time() - lc[1] < 0.3:
            return

        if not _chat_map:
            return

        self._close_pop()

        pop = tk.Toplevel(self.root)
        pop.overrideredirect(True)
        pop.attributes("-topmost", True)
        pop.configure(bg=ACC)

        box = tk.Frame(pop, bg=PANEL)
        box.pack(padx=1, pady=1)

        tk.Label(
            box, text="Calibrated builds", bg=PANEL, fg=KT,
            font=(FT, 10, "bold")
        ).pack(anchor="w", padx=12, pady=(8, 4))

        self._mg_list = tk.Frame(box, bg=PANEL)
        self._mg_list.pack(fill="x", padx=4)

        tk.Label(
            box,
            text="Recalibrate focuses the game and runs the Enter test.",
            bg=PANEL, fg=SUB, font=(FT, 8)
        ).pack(anchor="w", padx=12, pady=(4, 8))

        self._pop = pop
        self._pop_t = time.time()
        self._pop_kind = "manage"

        self._man_fill()

        if not self._pop:
            return

        pop.update_idletasks()

        w = pop.winfo_reqwidth()
        x = max(0, self.mnb.winfo_rootx() + self.mnb.winfo_width() - w)
        y = self.mnb.winfo_rooty() + self.mnb.winfo_height() + 6

        pop.geometry("+%d+%d" % (x, y))
        pop.bind("<Escape>", lambda e: self._close_pop())

    def _man_fill(self):
        if not self._pop or self._pop_kind != "manage":
            return

        lst = self._mg_list

        for w in lst.winfo_children():
            w.destroy()

        if not _chat_map:
            self._close_pop()
            return

        tk.Frame(lst, bg=PANEL, width=450, height=0).pack()

        running = {t["id"] for t in _tstate if t["id"]}
        items = sorted(
            _chat_map.items(),
            key=lambda kv: (
                kv[0] not in running, _chat_ver.get(kv[0], ""), kv[0]
            )
        )

        for bid, offs in items:
            row = tk.Frame(lst, bg=PANEL2)
            row.pack(fill="x", padx=4, pady=2)

            dl = tk.Label(
                row, text="\u2715", bg=PANEL2, fg=SUB,
                font=(FT, 10, "bold"), padx=10, cursor="hand2"
            )
            dl.pack(side="right")

            can = bid in running and not _learn["on"]

            rc = tk.Label(
                row, text="Recalibrate", bg=KB, fg=KT if can else DT,
                font=(FT, 9, "bold"), padx=10, pady=4,
                cursor="hand2" if can else ""
            )
            rc.pack(side="right", padx=(0, 4))

            txt = tk.Frame(row, bg=PANEL2)
            txt.pack(
                side="left", fill="x", expand=True, padx=(10, 6), pady=6
            )

            top = tk.Frame(txt, bg=PANEL2)
            top.pack(anchor="w")

            tk.Label(
                top, text=_chat_ver.get(bid) or "unknown version",
                bg=PANEL2, fg=KT, font=(FT, 10, "bold")
            ).pack(side="left")

            if bid in running:
                tk.Label(
                    top, text="  running", bg=PANEL2, fg=GRN,
                    font=(FT, 8, "bold")
                ).pack(side="left")

            tk.Label(
                txt,
                text="build %s  \u2022  offset %s" % (
                    bid, ", ".join("0x%X" % o for o in offs)
                ),
                bg=PANEL2, fg=SUB, font=(FT, 8)
            ).pack(anchor="w")

            if can:
                rc.bind("<Button-1>", lambda e, b=bid: self._man_redo(b))
                rc.bind("<Enter>", lambda e, l=rc: l.configure(bg=HOV))
                rc.bind("<Leave>", lambda e, l=rc: l.configure(bg=KB))

            st = {"arm": False}

            def kill(e, b=bid, dl=dl, st=st):
                if not st["arm"]:
                    st["arm"] = True
                    dl.configure(text="delete?", fg=RED)
                else:
                    self._man_del(b)

                return "break"

            dl.bind("<Button-1>", kill)

    def _man_redo(self, bid):
        self._close_pop()

        threading.Thread(
            target=_autocal_thread, args=(True, bid), daemon=True
        ).start()

    def _man_del(self, bid):
        _chat_map.pop(bid, None)
        _chat_ver.pop(bid, None)
        _chat_map_save()
        _chat_select()

        for t in _tstate:
            t["cal"] = bool(t["id"]) and _is_cal(t["id"])

        self._man_fill()

    def _cal_text(self):
        if _learn["on"]:
            return "Cancel"

        if _cal_need():
            return "Calibrate"

        if any(t["id"] for t in _tstate) or (_wow["h"] and CHAT_OFFSETS):
            return "\u2713 Calibrated"

        return "Calibrate"

    def _cal_click(self):
        if _learn["on"]:
            _learn["stop"] = True
            return

        threading.Thread(
            target=_autocal_thread, args=(self._cal_shift,), daemon=True
        ).start()
