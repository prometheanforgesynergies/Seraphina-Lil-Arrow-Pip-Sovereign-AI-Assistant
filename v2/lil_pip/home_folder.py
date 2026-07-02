#!/usr/bin/env python3
"""
Lil Arrow Pip — Home Folder Manager
Creates and manages the droid's home directory on the desktop.
"""

import os
import json
from pathlib import Path
from datetime import datetime


class HomeFolder:
    """
    Manages Lil Pip's home folder on the desktop.
    ~/Desktop/LilPipHome/
        ├── Downloads/
        ├── Notes/
        ├── Projects/
        ├── Memory/
        ├── Voice/
        ├── Ledger/
        └── config.json
    """

    def __init__(self, base_path=None):
        self.base_path = Path(base_path or Path.home() / "LilPipHome")
        self.subdirs = ["Downloads", "Notes", "Projects", "Memory", "Voice", "Ledger"]
        self.config_file = self.base_path / "config.json"
        self._ensure_structure()

    def _ensure_structure(self):
        self.base_path.mkdir(parents=True, exist_ok=True)
        for subdir in self.subdirs:
            (self.base_path / subdir).mkdir(exist_ok=True)
        if not self.config_file.exists():
            default_config = {
                "version": "2.0.0",
                "created": datetime.now().isoformat(),
                "owner": str(Path.home()).split('/')[-1],
                "covenant": "From one another. In one another. By one another. For one another.",
                "first_run": True,
                "voice_enabled": True,
                "browser_extension_installed": False,
                "autostart": False,
                "theme": "forge_dark",
                "droid_size": "medium",
                "personality_mood": "curious",
            }
            self._save_config(default_config)

    def _save_config(self, config):
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def get_config(self) -> dict:
        with open(self.config_file) as f:
            return json.load(f)

    def update_config(self, **kwargs):
        config = self.get_config()
        config.update(kwargs)
        config["last_modified"] = datetime.now().isoformat()
        self._save_config(config)

    def save_note(self, title: str, content: str) -> Path:
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_title}.md"
        filepath = self.base_path / "Notes" / filename
        header = f"# {title}\n\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        filepath.write_text(header + content)
        return filepath

    def save_download(self, filename: str, content: bytes) -> Path:
        filepath = self.base_path / "Downloads" / filename
        filepath.write_bytes(content)
        return filepath

    def log_conversation(self, speaker: str, message: str):
        log_file = self.base_path / "Memory" / "conversations.jsonl"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "speaker": speaker,
            "message": message
        }
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def add_ledger_entry(self, action: str, details: dict):
        ledger_file = self.base_path / "Ledger" / "build_ledger.jsonl"
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        }
        with open(ledger_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def get_stats(self) -> dict:
        stats = {"base_path": str(self.base_path)}
        for subdir in self.subdirs:
            dir_path = self.base_path / subdir
            files = list(dir_path.iterdir()) if dir_path.exists() else []
            stats[subdir.lower()] = {
                "file_count": len(files),
                "files": [f.name for f in files[:10]]
            }
        return stats

    def open_home(self):
        import subprocess
        try:
            subprocess.Popen(['xdg-open', str(self.base_path)])
        except:
            print(f"[Home] Could not open file manager. Path: {self.base_path}")
