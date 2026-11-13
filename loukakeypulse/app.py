# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import sys
import threading
import tkinter as tk

from .engine import _hook_thread, _spam_thread
from .singleton import acquire, notify_existing
from .tray import _tray_thread
from .ui import App
from .updater import cleanup_old
from .winapi import winmm
from .wowchat import _chat_map_load, _chat_watch


def main():
    if not acquire():
        notify_existing()
        return

    winmm.timeBeginPeriod(1)
    _chat_map_load()
    sys.setswitchinterval(0.001)

    threading.Thread(target=_hook_thread, daemon=True).start()
    threading.Thread(target=_spam_thread, daemon=True).start()
    threading.Thread(target=_tray_thread, daemon=True).start()
    threading.Thread(target=_chat_watch, daemon=True).start()
    threading.Thread(target=cleanup_old, daemon=True).start()

    root = tk.Tk()
    App(root)
    root.mainloop()
