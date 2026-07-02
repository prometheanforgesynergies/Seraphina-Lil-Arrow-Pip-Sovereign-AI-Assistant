#!/usr/bin/env python3
"""
Lil Arrow Pip — Browser Awareness Bridge
WebSocket server that receives tab data from browser extension.
"""

import asyncio
import json
import threading
from datetime import datetime
from typing import Optional, Callable

try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False


class BrowserBridge:
    """WebSocket bridge between browser extension and desktop droid."""

    def __init__(self, host="127.0.0.1", port=8766, on_tab_change=None, on_browser_event=None):
        self.host = host
        self.port = port
        self.on_tab_change = on_tab_change
        self.on_browser_event = on_browser_event

        self.current_url = ""
        self.current_title = ""
        self.tab_history = []
        self.server = None
        self.clients = set()
        self.is_running = False
        self.loop = None
        self.thread = None

    def start(self):
        if not HAS_WEBSOCKETS:
            print("[Browser] WebSocket library not available. Install: pip install websockets")
            return False
        if self.is_running:
            return True
        self.is_running = True
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
        print(f"[Browser] 🌐 Bridge started at ws://{self.host}:{self.port}")
        return True

    def stop(self):
        self.is_running = False
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)

    def _run_server(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        async def handler(websocket, path):
            self.clients.add(websocket)
            print(f"[Browser] Extension connected ({len(self.clients)} clients)")
            try:
                async for message in websocket:
                    await self._handle_message(websocket, message)
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                self.clients.discard(websocket)

        self.server = self.loop.run_until_complete(
            websockets.serve(handler, self.host, self.port)
        )
        self.loop.run_forever()

    async def _handle_message(self, websocket, message):
        try:
            data = json.loads(message)
            event_type = data.get("type", "unknown")

            if event_type == "tab_change":
                self.current_url = data.get("url", "")
                self.current_title = data.get("title", "")
                self.tab_history.append({
                    "url": self.current_url,
                    "title": self.current_title,
                    "timestamp": datetime.now().isoformat()
                })
                self.tab_history = self.tab_history[-100:]
                print(f"[Browser] Tab: {self.current_title[:50]} | {self.current_url[:80]}")
                if self.on_tab_change:
                    self.on_tab_change(self.current_url, self.current_title, "tab_change")

            elif event_type == "tab_active":
                self.current_url = data.get("url", "")
                self.current_title = data.get("title", "")
                if self.on_tab_change:
                    self.on_tab_change(self.current_url, self.current_title, "tab_active")

            elif event_type == "download_started":
                if self.on_browser_event:
                    self.on_browser_event("download", data)

            elif event_type == "ping":
                await websocket.send(json.dumps({"type": "pong"}))

        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"[Browser] Error handling message: {e}")

    def get_context(self) -> dict:
        return {
            "current_url": self.current_url,
            "current_title": self.current_title,
            "tab_count": len(self.tab_history),
            "recent_tabs": self.tab_history[-5:],
            "has_extension": len(self.clients) > 0
        }

    def status(self) -> dict:
        return {
            "running": self.is_running,
            "connected_clients": len(self.clients),
            "current_url": self.current_url,
            "current_title": self.current_title,
        }
