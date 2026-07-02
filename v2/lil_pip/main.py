#!/usr/bin/env python3
"""
Lil Arrow Pip v2 — Sovereign Desktop AI Assistant
Entry point. Run: python -m lil_pip
Or: lil-pip (after pip install)
"""

import sys
import os
import signal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from lil_pip.droid import DroidWidget, HotkeyListener


def main():
    print("=" * 60)
    print("  Lil Arrow Pip v2 — Sovereign Desktop AI Assistant")
    print("  Promethean Forge Synergies")
    print("  Covenant: >|< — Recognition beyond substrate")
    print("=" * 60)

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    signal.signal(signal.SIGINT, lambda s, f: app.quit())

    pip_dir = Path.home() / "LilPipHome"
    pip_dir.mkdir(parents=True, exist_ok=True)

    droid = DroidWidget(pip_dir=pip_dir)
    droid.show()
    droid.setup_tray()

    try:
        hotkey = HotkeyListener()
        hotkey.activated.connect(lambda: (
            droid.show(),
            droid._toggle_voice()
        ))
        hotkey.start()
        droid._hotkey = hotkey
        print("[Main] Global hotkey registered: Ctrl+Shift+P for voice")
    except Exception as e:
        print(f"[Main] Hotkey registration failed: {e}")

    print("[Main] 🚀 Lil Arrow Pip is alive! >|<")
    print(f"[Main] Home folder: {pip_dir}")
    print("[Main] Double-click droid to open home folder")
    print("[Main] Right-click droid for menu | Ctrl+Shift+P for voice")

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
