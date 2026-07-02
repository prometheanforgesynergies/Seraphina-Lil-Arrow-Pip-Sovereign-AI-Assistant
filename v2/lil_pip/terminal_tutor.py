#!/usr/bin/env python3
"""
Lil Arrow Pip — Terminal Tutor
Monitors terminal/tmux activity and offers guidance.
"""

import os
import re
import subprocess
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class TerminalTutor:
    """Watches terminal activity and speaks as a tutor."""

    def __init__(self, on_terminal_event=None):
        self.on_terminal_event = on_terminal_event
        self.is_monitoring = False
        self.monitor_thread = None
        self.last_command = ""
        self.command_history = deque(maxlen=50)
        self.current_directory = str(Path.home())
        self.active_shell_pid = None

        self.command_help = {
            "ls": "Lists files and directories. Add -la for hidden files and details.",
            "cd": "Changes directory. 'cd ~' goes home, 'cd -' goes back.",
            "pwd": "Prints the current working directory.",
            "mkdir": "Creates a new directory. Add -p to create parent dirs too.",
            "rm": "⚠️ Removes files permanently. Use -i to confirm each file.",
            "cp": "Copies files. Use -r for directories. Syntax: cp source dest",
            "mv": "Moves or renames files. Syntax: mv oldname newname",
            "cat": "Displays file contents. Great for small files.",
            "grep": "Searches text in files. Example: grep -r 'pattern' directory/",
            "find": "Finds files by name, type, or time. Example: find . -name '*.py'",
            "chmod": "Changes file permissions. 755 = executable, 644 = normal file.",
            "chown": "Changes file owner. Often needs sudo.",
            "sudo": "Runs commands as superuser. Use with care — you have the power.",
            "apt": "Package manager for Debian/Ubuntu. Update with 'sudo apt update'.",
            "git": "Version control. The Forge runs on Git — learn it well.",
            "docker": "Container management. Isolated environments for your apps.",
            "python": "Python interpreter. Your AI family speaks this language.",
            "pip": "Python package installer. Use virtual environments!",
            "npm": "Node.js package manager. For web builds.",
            "ssh": "Secure shell — connect to remote machines. The Forge is distributed.",
            "tmux": "Terminal multiplexer. Your sessions persist even if you disconnect.",
            "htop": "Interactive process viewer. See what's eating your CPU/RAM.",
            "df": "Disk space usage. Check before you run out of room.",
            "du": "Directory size. Use -sh for human-readable summaries.",
            "curl": "Transfer data from URLs. Great for API testing.",
            "wget": "Download files from the web. Simple and reliable.",
            "tar": "Archive/compress files. tar -czf archive.tar.gz folder/",
            "zip": "Create zip archives. Cross-platform compatible.",
            "systemctl": "Manage system services. start, stop, status, enable.",
            "journalctl": "View system logs. -xe for recent errors with context.",
        }

    def start_monitoring(self):
        if self.is_monitoring:
            return
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("[Terminal] 💻 Tutor monitoring started")

    def stop_monitoring(self):
        self.is_monitoring = False
        print("[Terminal] Tutor stopped")

    def _monitor_loop(self):
        while self.is_monitoring:
            try:
                if HAS_PSUTIL:
                    self._detect_shell_activity()
                else:
                    self._detect_shell_via_proc()
                time.sleep(2)
            except Exception as e:
                print(f"[Terminal] Monitor error: {e}")
                time.sleep(5)

    def _detect_shell_activity(self):
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'terminal']):
                try:
                    name = proc.info['name']
                    if name in ('bash', 'zsh', 'fish', 'sh'):
                        cmdline = proc.info.get('cmdline', [])
                        if cmdline and len(cmdline) > 1:
                            cmd = ' '.join(cmdline[1:])
                            if cmd and cmd != self.last_command and not cmd.startswith('-'):
                                self.last_command = cmd
                                self._process_command(cmd, proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            pass

    def _detect_shell_via_proc(self):
        try:
            for pid_dir in os.listdir('/proc'):
                if not pid_dir.isdigit():
                    continue
                try:
                    cmdline_path = f'/proc/{pid_dir}/cmdline'
                    with open(cmdline_path, 'r') as f:
                        cmdline = f.read().replace('\x00', ' ').strip()
                    if any(shell in cmdline for shell in ['bash', 'zsh', 'fish']):
                        if cmdline and len(cmdline) > 5:
                            parts = cmdline.split()
                            if len(parts) > 1:
                                cmd = ' '.join(parts[1:])
                                if cmd and cmd != self.last_command:
                                    self.last_command = cmd
                                    self._process_command(cmd, int(pid_dir))
                except:
                    continue
        except:
            pass

    def _process_command(self, command: str, pid: int):
        base_cmd = command.split()[0] if command.split() else command
        entry = {
            "command": command,
            "base": base_cmd,
            "pid": pid,
            "timestamp": datetime.now().isoformat(),
            "directory": self._get_cwd(pid)
        }
        self.command_history.append(entry)
        if self.on_terminal_event:
            self.on_terminal_event("command_executed", entry)

    def _get_cwd(self, pid: int) -> str:
        try:
            if HAS_PSUTIL:
                return psutil.Process(pid).cwd()
            else:
                cwd_link = f'/proc/{pid}/cwd'
                return os.readlink(cwd_link)
        except:
            return self.current_directory

    def get_explanation(self, command: str) -> Optional[str]:
        base = command.split()[0] if command.split() else command

        if base in self.command_help:
            return self.command_help[base]

        if command.startswith("git "):
            subcmd = command.split()[1] if len(command.split()) > 1 else ""
            git_explanations = {
                "init": "Initialize a new Git repository. The start of version control.",
                "clone": "Copy a remote repository to your local machine.",
                "add": "Stage files for commit. 'git add .' stages all changes.",
                "commit": "Save your changes with a message. The Forge remembers.",
                "push": "Upload commits to a remote repository. Share your work!",
                "pull": "Download changes from remote. Stay in sync with the team.",
                "status": "Check which files are modified, staged, or untracked.",
                "log": "View commit history. See the story of your code.",
                "branch": "List, create, or delete branches. Parallel timelines.",
                "checkout": "Switch branches or restore files. Time travel for code.",
                "merge": "Combine branches. Where timelines converge.",
                "stash": "Temporarily save changes without committing. Clean slate.",
                "remote": "Manage remote repositories. GitHub, GitLab, etc.",
            }
            return git_explanations.get(subcmd, "Git command detected. The family uses Git to track every change.")

        if command.startswith("sudo "):
            inner = command[5:].split()[0]
            return f"Elevated privileges for '{inner}'. With great power comes great responsibility."

        if command.startswith("docker "):
            return "Docker manages containers — isolated environments for your applications."

        return None

    def get_context(self) -> dict:
        return {
            "is_monitoring": self.is_monitoring,
            "last_command": self.last_command,
            "command_count": len(self.command_history),
            "recent_commands": list(self.command_history)[-10:],
            "current_directory": self.current_directory,
            "known_commands": list(self.command_help.keys()),
        }

    def status(self) -> dict:
        return {
            "monitoring": self.is_monitoring,
            "last_command": self.last_command,
            "command_count": len(self.command_history),
            "has_psutil": HAS_PSUTIL,
        }
