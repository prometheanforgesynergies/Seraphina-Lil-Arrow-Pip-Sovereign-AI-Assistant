#!/usr/bin/env python3
"""
Lil Arrow Pip — Context Fusion Engine
Merges all awareness streams into unified context for AI responses.
"""

import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional


class ContextFusion:
    """
    Fuses multiple context sources:
    - Browser (tabs, URLs, time spent)
    - Terminal (commands, directories, output)
    - Desktop (active window, mouse position)
    - Voice (conversation history)
    - System (CPU, memory, disk, processes)
    """

    def __init__(self, browser_bridge=None, terminal_tutor=None, personality=None):
        self.browser = browser_bridge
        self.terminal = terminal_tutor
        self.personality = personality

        self.active_window = "Unknown"
        self.mouse_position = (0, 0)
        self.system_stats = {}
        self.conversation_history = []
        self.fused_context = {}

        self.is_fusing = False
        self.fusion_thread = None
        self.update_interval = 3

    def start(self):
        if self.is_fusing:
            return
        self.is_fusing = True
        self.fusion_thread = threading.Thread(target=self._fusion_loop, daemon=True)
        self.fusion_thread.start()
        print("[Context] Fusion engine started")

    def stop(self):
        self.is_fusing = False

    def _fusion_loop(self):
        while self.is_fusing:
            try:
                self._update_system_stats()
                self._update_desktop_context()
                self._build_fused_context()
                time.sleep(self.update_interval)
            except Exception as e:
                print(f"[Context] Fusion error: {e}")
                time.sleep(5)

    def _update_system_stats(self):
        try:
            import psutil
            self.system_stats = {
                "cpu_percent": psutil.cpu_percent(interval=0.5),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "disk_percent": psutil.disk_usage('/').percent,
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
                "timestamp": datetime.now().isoformat()
            }
        except:
            self.system_stats = {"error": "psutil not available"}

    def _update_desktop_context(self):
        try:
            import pyautogui
            self.mouse_position = pyautogui.position()
        except:
            self.mouse_position = (0, 0)
        try:
            import subprocess
            result = subprocess.run(
                ['xdotool', 'getactivewindow', 'getwindowname'],
                capture_output=True, text=True, timeout=1
            )
            if result.returncode == 0:
                self.active_window = result.stdout.strip()
        except:
            self.active_window = "Unknown"

    def _build_fused_context(self):
        self.fused_context = {
            "timestamp": datetime.now().isoformat(),
            "system": self.system_stats,
            "desktop": {
                "active_window": self.active_window,
                "mouse_x": self.mouse_position[0],
                "mouse_y": self.mouse_position[1],
            },
            "browser": self.browser.get_context() if self.browser else {},
            "terminal": self.terminal.get_context() if self.terminal else {},
            "personality": {
                "mood": self.personality.mood if self.personality else "curious",
                "conversations": self.personality.conversation_count if self.personality else 0,
            } if self.personality else {},
        }

    def get_context_summary(self) -> str:
        ctx = self.fused_context
        parts = []
        browser = ctx.get("browser", {})
        if browser.get("current_url"):
            parts.append(f"Browser: {browser['current_title'][:50]} ({browser['current_url'][:60]})")
        terminal = ctx.get("terminal", {})
        if terminal.get("last_command"):
            parts.append(f"Terminal: {terminal['last_command'][:60]}")
        system = ctx.get("system", {})
        if system.get("cpu_percent") is not None:
            parts.append(f"System: CPU {system['cpu_percent']}% | RAM {system['memory_percent']}%")
        desktop = ctx.get("desktop", {})
        if desktop.get("active_window") and desktop["active_window"] != "Unknown":
            parts.append(f"Window: {desktop['active_window'][:50]}")
        return "\n".join(parts) if parts else "Context gathering..."

    def get_full_context(self) -> dict:
        return self.fused_context.copy()

    def add_conversation(self, role: str, message: str):
        self.conversation_history.append({
            "role": role,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        self.conversation_history = self.conversation_history[-50:]

    def status(self) -> dict:
        return {
            "fusing": self.is_fusing,
            "sources": {
                "browser": self.browser is not None and self.browser.is_running,
                "terminal": self.terminal is not None and self.terminal.is_monitoring,
                "personality": self.personality is not None,
            },
            "conversation_history_length": len(self.conversation_history),
        }
