# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import os
import queue
import threading
import time
import tkinter as tk
import webbrowser
from tkinter import messagebox

from . import __version__, updater
from .config import APP_NAME, updates_get, updates_set
from .singleton import release
from .theme import ACC, BG, FT, HOV, KT, PANEL, PANEL2, RED, SUB
from .tray import _tray_remove


class UpdateMixin:
    def _upd_init(self):
        self._upd_q = queue.Queue()
        self._upd_busy = False
        self._upd_win = None
        self._upd_info = None
        self._upd_seen = set()
        self._upd_cancel = threading.Event()
        self.root.after(1000, self._upd_poll)
        self.root.after(8000, self._upd_auto)

    def _upd_auto(self):
        try:
            s = updates_get()
            due = time.time() - float(s.get("last_check", 0)) > 6 * 3600

            if s.get("auto_check", True) and due:
                self._upd_start(False)
        except Exception:
            pass

        self.root.after(30 * 60 * 1000, self._upd_auto)

    def _upd_start(self, manual):
        if self._upd_busy:
            return

        self._upd_busy = True
        threading.Thread(
            target=self._upd_worker, args=(manual,), daemon=True
        ).start()

    def _upd_worker(self, manual):
        try:
            info = updater.check()
            self._upd_q.put(("checked", manual, info, None))
        except Exception as e:
            self._upd_q.put(("checked", manual, None, str(e)))

    def _upd_poll(self):
        try:
            while True:
                m = self._upd_q.get_nowait()

                if m[0] == "checked":
                    self._upd_checked(m[1], m[2], m[3])
                elif m[0] == "progress":
                    self._upd_progress(m[1])
                elif m[0] == "downloaded":
                    self._upd_apply(m[1])
                elif m[0] == "failed":
                    self._upd_failed(m[1])

        except queue.Empty:
            pass

        self.root.after(200, self._upd_poll)

    def _upd_checked(self, manual, info, err):
        self._upd_busy = False

        if err:
            if manual:
                messagebox.showwarning(
                    APP_NAME, "Could not check for updates.\n\n" + err
                )
            return

        updates_set(last_check=time.time())

        if info is None:
            if manual:
                messagebox.showinfo(
                    APP_NAME,
                    "You are up to date (version %s)." % __version__
                )
            return

        if not manual:
            skipped = updates_get().get("skipped")

            if info["version"] == skipped or info["version"] in self._upd_seen:
                return

        self._upd_seen.add(info["version"])
        self._upd_show(info)

    def _upd_show(self, info):
        if self._upd_win:
            return

        win = tk.Toplevel(self.root)
        win.title("%s update" % APP_NAME)
        win.configure(bg=BG)
        win.attributes("-topmost", True)
        win.resizable(False, False)
        win.protocol("WM_DELETE_WINDOW", self._upd_close)

        self._upd_win = win
        self._upd_info = dict(info)
        self._upd_cancel.clear()

        tk.Label(
            win, text="Update available", bg=BG, fg="#fff",
            font=(FT, 15, "bold")
        ).pack(anchor="w", padx=20, pady=(18, 2))

        tk.Label(
            win,
            text="Version %s is available - you have %s" % (
                info["version"], __version__
            ),
            bg=BG, fg=SUB, font=(FT, 10)
        ).pack(anchor="w", padx=20)

        box = tk.Frame(win, bg=PANEL)
        box.pack(fill="both", expand=True, padx=20, pady=12)

        txt = tk.Text(
            box, width=64, height=14, bg=PANEL, fg=KT, bd=0, wrap="word",
            font=(FT, 10), padx=12, pady=10, highlightthickness=0
        )
        bar = tk.Scrollbar(box, command=txt.yview)
        txt.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)
        txt.insert(
            "1.0", updater.plain_notes(info["notes"]) or "No changelog provided."
        )
        txt.configure(state="disabled")

        self._upd_bar = tk.Canvas(
            win, height=8, bg=PANEL2, highlightthickness=0
        )
        self._upd_msg = tk.Label(
            win, text="", bg=BG, fg=SUB, font=(FT, 9), anchor="w"
        )
        self._upd_msg.pack(fill="x", padx=20)

        row = tk.Frame(win, bg=BG)
        row.pack(fill="x", padx=20, pady=(8, 16))

        def mk(text, cmd, bg, fg, side):
            b = tk.Button(
                row, text=text, command=cmd, bg=bg, fg=fg,
                activebackground=HOV, activeforeground=KT, relief="flat",
                bd=0, font=(FT, 10, "bold"), padx=16, pady=8,
                cursor="hand2"
            )
            b.pack(side=side, padx=(8, 0) if side == "right" else (0, 8))
            return b

        installable = bool(
            updater.can_install() and info.get("exe") and info.get("sha")
        )

        self._upd_go_btn = mk(
            "Update now" if installable else "Open download page",
            self._upd_go, ACC, "#fff", "right"
        )
        self._upd_later_btn = mk("Later", self._upd_close, PANEL2, KT, "right")
        self._upd_skip_btn = mk(
            "Skip this version", self._upd_skip, PANEL2, SUB, "left"
        )

        win.update_idletasks()
        x = (win.winfo_screenwidth() - win.winfo_reqwidth()) // 2
        y = (win.winfo_screenheight() - win.winfo_reqheight()) // 3
        win.geometry("+%d+%d" % (max(0, x), max(0, y)))

    def _upd_close(self):
        self._upd_cancel.set()
        win, self._upd_win = self._upd_win, None

        if win:
            win.destroy()

    def _upd_skip(self):
        if self._upd_info:
            updates_set(skipped=self._upd_info["version"])

        self._upd_close()

    def _upd_go(self):
        info = self._upd_info

        if not info:
            return

        installable = bool(
            updater.can_install() and info.get("exe") and info.get("sha")
        )

        if not installable:
            webbrowser.open(info["page"])
            self._upd_close()
            return

        self._upd_cancel.clear()
        self._upd_go_btn.configure(state="disabled")
        self._upd_skip_btn.configure(state="disabled")
        self._upd_later_btn.configure(text="Cancel")
        self._upd_bar.pack(fill="x", padx=20, pady=(0, 6), before=self._upd_msg)
        self._upd_msg.configure(text="Downloading...", fg=SUB)

        threading.Thread(
            target=self._upd_dl_worker, args=(info,), daemon=True
        ).start()

    def _upd_dl_worker(self, info):
        dest = updater.exe_path() + ".new"

        try:
            updater.download(
                info, dest,
                lambda f: self._upd_q.put(("progress", f)),
                self._upd_cancel
            )
            self._upd_q.put(("downloaded", dest))
        except InterruptedError:
            self._upd_q.put(("failed", None))
        except Exception as e:
            self._upd_q.put(("failed", str(e)))

    def _upd_progress(self, frac):
        if not self._upd_win:
            return

        w = max(self._upd_bar.winfo_width(), 10)
        self._upd_bar.delete("all")
        self._upd_bar.create_rectangle(0, 0, w * frac, 8, fill=ACC, outline="")
        self._upd_msg.configure(
            text="Downloading... %d%%" % int(frac * 100), fg=SUB
        )

    def _upd_apply(self, path):
        if not self._upd_win:
            try:
                os.remove(path)
            except OSError:
                pass
            return

        self._upd_msg.configure(text="Installing...", fg=SUB)

        try:
            updater.apply(path)
        except Exception as e:
            self._upd_failed("Could not install the update: %s" % e)
            return

        self._upd_restart()

    def _upd_restart(self):
        self.save()
        _tray_remove()
        release()
        updater.relaunch()
        os._exit(0)

    def _upd_failed(self, msg):
        if not self._upd_win or msg is None:
            return

        self._upd_info["exe"] = None
        self._upd_msg.configure(
            text="%s. Press the button to open the download page." % msg,
            fg=RED
        )
        self._upd_go_btn.configure(
            state="normal", text="Open download page"
        )
        self._upd_skip_btn.configure(state="normal")
        self._upd_later_btn.configure(text="Later")
