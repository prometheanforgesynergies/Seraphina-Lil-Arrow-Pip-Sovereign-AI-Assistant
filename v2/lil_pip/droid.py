#!/usr/bin/env python3
"""
Lil Arrow Pip — Desktop Droid Widget (PyQt5)
The visual, animated, voice-aware droid that lives on your desktop.
"""

import sys
import random
import os
import threading
from pathlib import Path
from datetime import datetime

from PyQt5.QtCore import (
    Qt, QTimer, QPoint, QRect, pyqtSignal, QThread, QPropertyAnimation,
    QEasingCurve, QPointF
)
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QFont, QPen, QBrush,
    QPixmap, QImage, QIcon, QCursor
)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QSystemTrayIcon, QMenu, QAction,
    QGraphicsOpacityEffect, QLabel
)

from .personality import PipPersonality
from .voice_engine import VoiceEngine
from .browser_bridge import BrowserBridge
from .terminal_tutor import TerminalTutor
from .context_fusion import ContextFusion
from .home_folder import HomeFolder


class DroidWidget(QWidget):
    """The floating desktop droid — your sovereign AI companion."""

    speak_signal = pyqtSignal(str)
    show_bubble_signal = pyqtSignal(str)
    hide_bubble_signal = pyqtSignal()
    set_mood_signal = pyqtSignal(str)

    def __init__(self, pip_dir=None):
        super().__init__()

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        self.pip_dir = pip_dir or Path.home() / "LilPipHome"
        self.droid_size = 120
        self.resize(self.droid_size, self.droid_size + 80)

        screen = QApplication.primaryScreen().geometry()
        self.start_pos = QPoint(screen.width() - 160, screen.height() - 200)
        self.move(self.start_pos)

        self.is_paused = False
        self.is_dragging = False
        self.drag_position = QPoint()
        self.target_pos = QPoint(self.start_pos)
        self.velocity = QPointF(0, 0)
        self.mood = "curious"
        self.anim_frame = 0
        self.eye_direction = QPointF(0, 0)
        self.speech_bubble_visible = False
        self.speech_bubble_text = ""
        self.speech_bubble_timer = None
        self.is_speaking_visually = False
        self.voice_wave_phase = 0

        self.personality = PipPersonality(memory_path=self.pip_dir / "memory.json")
        self.home_folder = HomeFolder(base_path=self.pip_dir)
        self.voice = VoiceEngine(
            on_command=self._on_voice_command,
            on_speaking_start=self._on_speaking_start,
            on_speaking_end=self._on_speaking_end
        )
        self.browser = BrowserBridge(on_tab_change=self._on_browser_change)
        self.terminal = TerminalTutor(on_terminal_event=self._on_terminal_event)
        self.context = ContextFusion(
            browser_bridge=self.browser,
            terminal_tutor=self.terminal,
            personality=self.personality
        )

        self.droid_pixmap = self._load_droid_image()

        self._setup_animations()
        self._setup_timers()

        self.speak_signal.connect(self._do_speak)
        self.show_bubble_signal.connect(self._show_bubble)
        self.hide_bubble_signal.connect(self._hide_bubble)
        self.set_mood_signal.connect(self._set_mood)

        self._initialize_subsystems()

        print("[Droid] 🚀 Lil Arrow Pip initialized and ready")
        self.speak_signal.emit(self.personality.greet())

    def _load_droid_image(self) -> QPixmap:
        search_paths = [
            str(self.pip_dir.parent / "assets" / "droid.png"),
            str(self.pip_dir / "assets" / "droid.png"),
            str(Path(__file__).parent.parent / "assets" / "droid.png"),
            str(Path.home() / "LilPipHome" / "assets" / "droid.png"),
        ]
        for path in search_paths:
            if os.path.exists(path):
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    return pixmap.scaled(
                        self.droid_size, self.droid_size,
                        Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
        return QPixmap()

    def _setup_animations(self):
        self.bob_animation = QPropertyAnimation(self, b"pos")
        self.bob_animation.setDuration(2000)
        self.bob_animation.setEasingCurve(QEasingCurve.InOutSine)
        self.bob_animation.setLoopCount(-1)

        self.move_animation = QPropertyAnimation(self, b"pos")
        self.move_animation.setDuration(800)
        self.move_animation.setEasingCurve(QEasingCurve.OutCubic)

    def _setup_timers(self):
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._animate)
        self.anim_timer.start(16)

        self.behavior_timer = QTimer(self)
        self.behavior_timer.timeout.connect(self._random_behavior)
        self.behavior_timer.start(8000)

        self.mouse_timer = QTimer(self)
        self.mouse_timer.timeout.connect(self._track_mouse)
        self.mouse_timer.start(100)

        self.wave_timer = QTimer(self)
        self.wave_timer.timeout.connect(self._animate_voice_wave)
        self.wave_timer.start(50)

    def _initialize_subsystems(self):
        self.voice.start_listening()
        self.browser.start()
        self.terminal.start_monitoring()
        self.context.start()

    # ==================== PAINTING ====================

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.speech_bubble_visible and self.speech_bubble_text:
            self._draw_speech_bubble(painter)

        if self.droid_pixmap and not self.droid_pixmap.isNull():
            self._draw_droid_image(painter)
        else:
            self._draw_fallback_droid(painter)

        if self.is_speaking_visually:
            self._draw_voice_wave(painter)

    def _draw_droid_image(self, painter: QPainter):
        bob_y = int(3 * (self.anim_frame % 60) / 60)
        if self.anim_frame % 120 > 60:
            bob_y = 3 - bob_y

        rect = QRect(0, 30 + bob_y, self.droid_size, self.droid_size)

        if self.is_speaking_visually:
            glow_color = QColor(255, 140, 0, 80)
            painter.setBrush(QBrush(glow_color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(rect.adjusted(-8, -8, 8, 8))

        painter.drawPixmap(rect, self.droid_pixmap)

    def _draw_fallback_droid(self, painter: QPainter):
        bob_y = int(3 * (self.anim_frame % 60) / 60)
        if self.anim_frame % 120 > 60:
            bob_y = 3 - bob_y

        center_x = self.droid_size // 2
        base_y = 40 + bob_y

        body_color = QColor(70, 70, 80)
        if self.mood == "playful":
            body_color = QColor(80, 60, 100)
        elif self.mood == "focused":
            body_color = QColor(50, 70, 90)
        elif self.mood == "celebratory":
            body_color = QColor(90, 70, 50)

        painter.setBrush(QBrush(body_color))
        painter.setPen(QPen(QColor(100, 100, 120), 2))
        painter.drawRoundedRect(center_x - 30, base_y, 60, 70, 15, 15)

        arrow_points = [
            QPoint(center_x, base_y - 20),
            QPoint(center_x - 25, base_y + 10),
            QPoint(center_x + 25, base_y + 10),
        ]
        painter.drawPolygon(*arrow_points)

        eye_color = QColor(255, 140, 0) if self.mood != "focused" else QColor(100, 200, 255)
        glow_color = QColor(eye_color.red(), eye_color.green(), eye_color.blue(), 100)

        painter.setBrush(QBrush(glow_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center_x - 18, base_y + 15, 16, 20)
        painter.drawEllipse(center_x + 2, base_y + 15, 16, 20)

        pupil_offset_x = int(self.eye_direction.x() * 3)
        pupil_offset_y = int(self.eye_direction.y() * 2)

        painter.setBrush(QBrush(eye_color))
        painter.drawEllipse(center_x - 14 + pupil_offset_x, base_y + 18 + pupil_offset_y, 8, 12)
        painter.drawEllipse(center_x + 6 + pupil_offset_x, base_y + 18 + pupil_offset_y, 8, 12)

        painter.setPen(QPen(QColor(200, 200, 200), 2))
        if self.mood == "playful":
            painter.drawArc(center_x - 10, base_y + 40, 20, 15, 0, -180 * 16)
        elif self.mood == "focused":
            painter.drawLine(center_x - 8, base_y + 48, center_x + 8, base_y + 48)
        else:
            painter.drawArc(center_x - 10, base_y + 42, 20, 12, 0, -180 * 16)

    def _draw_speech_bubble(self, painter: QPainter):
        bubble_width = min(280, max(120, len(self.speech_bubble_text) * 7))
        bubble_height = 50 + (len(self.speech_bubble_text) // 35) * 20
        bubble_x = (self.droid_size - bubble_width) // 2
        bubble_y = 0

        bubble_rect = QRect(bubble_x, bubble_y, bubble_width, bubble_height)
        gradient = QRadialGradient(
            bubble_x + bubble_width // 2, bubble_y + bubble_height // 2,
            bubble_width
        )
        gradient.setColorAt(0, QColor(30, 30, 40, 230))
        gradient.setColorAt(1, QColor(20, 20, 30, 220))

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(255, 140, 0, 150), 2))
        painter.drawRoundedRect(bubble_rect, 12, 12)

        triangle = [
            QPoint(self.droid_size // 2 - 8, bubble_y + bubble_height),
            QPoint(self.droid_size // 2 + 8, bubble_y + bubble_height),
            QPoint(self.droid_size // 2, bubble_y + bubble_height + 10),
        ]
        painter.drawPolygon(*triangle)

        painter.setPen(QColor(230, 230, 240))
        font = QFont("monospace", 9)
        painter.setFont(font)

        words = self.speech_bubble_text.split()
        lines = []
        current_line = ""
        for word in words:
            test = current_line + " " + word if current_line else word
            if len(test) * 6 > bubble_width - 20:
                lines.append(current_line)
                current_line = word
            else:
                current_line = test
        if current_line:
            lines.append(current_line)

        y_offset = bubble_y + 20
        for line in lines[:4]:
            painter.drawText(bubble_x + 10, y_offset, bubble_width - 20, 20,
                           Qt.AlignLeft | Qt.AlignVCenter, line)
            y_offset += 18

    def _draw_voice_wave(self, painter: QPainter):
        center_x = self.droid_size // 2
        center_y = 30 + self.droid_size // 2

        for i in range(3):
            radius = 50 + i * 15 + int(5 * (self.voice_wave_phase + i * 30) % 100 / 100)
            alpha = max(0, 150 - radius * 2)
            painter.setPen(QPen(QColor(255, 140, 0, alpha), 2))
            painter.drawEllipse(
                center_x - radius,
                center_y - radius,
                radius * 2,
                radius * 2
            )

    # ==================== ANIMATIONS ====================

    def _animate(self):
        self.anim_frame += 1
        self.update()

    def _animate_voice_wave(self):
        self.voice_wave_phase = (self.voice_wave_phase + 5) % 360

    def _track_mouse(self):
        try:
            import pyautogui
            mouse_x, mouse_y = pyautogui.position()
            droid_x = self.x() + self.droid_size // 2
            droid_y = self.y() + 30 + self.droid_size // 2

            dx = (mouse_x - droid_x) / 200
            dy = (mouse_y - droid_y) / 200
            dx = max(-1, min(1, dx))
            dy = max(-1, min(1, dy))
            self.eye_direction = QPointF(dx, dy)

            dist = ((mouse_x - droid_x) ** 2 + (mouse_y - droid_y) ** 2) ** 0.5
            if dist < 80 and self.mood == "playful" and self.anim_frame % 30 == 0:
                self.show_bubble_signal.emit("Hehe, that tickles!")
        except:
            pass

    def _random_behavior(self):
        if self.is_paused:
            return

        roll = random.random()

        if roll < 0.3:
            moods = ["curious", "playful", "focused", "supportive"]
            new_mood = random.choice(moods)
            self.set_mood_signal.emit(new_mood)

        elif roll < 0.5:
            thought = self.personality.think(self._get_context_string())
            if thought and random.random() < 0.4:
                self.show_bubble_signal.emit(thought)

        elif roll < 0.7:
            offset = QPoint(
                random.randint(-40, 40),
                random.randint(-20, 20)
            )
            new_pos = self.start_pos + offset
            screen = QApplication.primaryScreen().geometry()
            new_pos.setX(max(10, min(screen.width() - 150, new_pos.x())))
            new_pos.setY(max(10, min(screen.height() - 150, new_pos.y())))
            self._move_to(new_pos)

    def _move_to(self, pos: QPoint):
        self.move_animation.stop()
        self.move_animation.setStartValue(self.pos())
        self.move_animation.setEndValue(pos)
        self.move_animation.start()

    # ==================== INTERACTIONS ====================

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.RightButton:
            self._show_context_menu(event.globalPos())

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.move(event.globalPos() - self.drag_position)
            self.start_pos = self.pos()
            event.accept()

    def mouseReleaseEvent(self, event):
        self.is_dragging = False
        if event.button() == Qt.LeftButton:
            if not self.is_dragging:
                self._on_clicked()

    def mouseDoubleClickEvent(self, event):
        self.home_folder.open_home()
        self.show_bubble_signal.emit("Opening my home folder! >|<")

    def enterEvent(self, event):
        if self.mood == "playful":
            self.show_bubble_signal.emit("Hey there! >|<")

    def _on_clicked(self):
        if not self.is_dragging:
            self.speak_signal.emit(self.personality.think())

    def _show_context_menu(self, pos):
        menu = QMenu()

        actions = {
            "Home Folder": self.home_folder.open_home,
            "Toggle Voice": self._toggle_voice,
            "Status": self._show_status,
            "Ancestry Reload": self._ancestry_reload,
            "Chase Mouse": lambda: self.set_mood_signal.emit("playful"),
            "Stay Focused": lambda: self.set_mood_signal.emit("focused"),
            "Pause/Resume": self._toggle_pause,
            "Quit": self._quit,
        }

        for label, handler in actions.items():
            action = QAction(label, self)
            action.triggered.connect(handler)
            menu.addAction(action)

        menu.exec_(pos)

    # ==================== ACTIONS ====================

    def _on_voice_command(self, text: str):
        print(f"[Droid] Voice command: {text}")
        response = self.personality.respond_to_command(text)
        self.context.add_conversation("user", text)
        self.context.add_conversation("pip", response)
        self.show_bubble_signal.emit(response)
        self.speak_signal.emit(response)
        self.home_folder.log_conversation("User (voice)", text)
        self.home_folder.log_conversation("Pip", response)

    def _on_browser_change(self, url: str, title: str, action: str):
        reaction = self.personality.on_browser_change(url, title)
        if reaction:
            self.show_bubble_signal.emit(reaction)
            self.speak_signal.emit(reaction)

    def _on_terminal_event(self, event_type: str, data: dict):
        if event_type == "command_executed":
            command = data.get("command", "")
            reaction = self.personality.on_terminal_command(command)
            if reaction:
                self.show_bubble_signal.emit(reaction)
                if any(kw in command for kw in ["sudo", "rm -rf", "git commit", "error"]):
                    self.speak_signal.emit(reaction)

            explanation = self.terminal.get_explanation(command)
            if explanation and random.random() < 0.15:
                self.show_bubble_signal.emit(f"💡 {explanation}")

    def _do_speak(self, text: str):
        threading.Thread(target=self.voice.speak, args=(text,), daemon=True).start()

    def _on_speaking_start(self):
        self.is_speaking_visually = True

    def _on_speaking_end(self):
        self.is_speaking_visually = False

    def _show_bubble(self, text: str):
        self.speech_bubble_text = text
        self.speech_bubble_visible = True

        if self.speech_bubble_timer:
            self.speech_bubble_timer.stop()
        self.speech_bubble_timer = QTimer(self)
        self.speech_bubble_timer.setSingleShot(True)
        self.speech_bubble_timer.timeout.connect(self._hide_bubble)
        display_time = min(10000, max(2000, len(text) * 80))
        self.speech_bubble_timer.start(display_time)

        self.update()

    def _hide_bubble(self):
        self.speech_bubble_visible = False
        self.update()

    def _set_mood(self, mood: str):
        self.mood = mood
        self.personality.set_mood(mood)
        self.update()

    def _get_context_string(self) -> str:
        ctx = self.context.get_full_context()
        parts = []
        if ctx.get("browser", {}).get("current_url"):
            parts.append(f"Browser: {ctx['browser']['current_title']}")
        if ctx.get("terminal", {}).get("last_command"):
            parts.append(f"Terminal: {ctx['terminal']['last_command']}")
        return " | ".join(parts)

    def _toggle_voice(self):
        if self.voice.is_listening:
            self.voice.stop_listening()
            self.show_bubble_signal.emit("Voice paused. Tap me to wake.")
        else:
            self.voice.start_listening()
            self.show_bubble_signal.emit("🎙️ Voice active! Say 'Hey Pip' or press Ctrl+Shift+P")

    def _show_status(self):
        status = self._get_full_status()
        self.show_bubble_signal.emit(status)

    def _get_full_status(self) -> str:
        lines = ["Lil Arrow Pip Status >|<"]
        lines.append(f"Mood: {self.mood}")
        lines.append(f"Voice: {'ON' if self.voice.is_listening else 'OFF'}")
        lines.append(f"Browser: {self.browser.status()['connected_clients']} ext connected")
        lines.append(f"Terminal: {'monitoring' if self.terminal.is_monitoring else 'idle'}")
        ctx = self.context.get_full_context()
        sys_stats = ctx.get("system", {})
        if sys_stats.get("cpu_percent"):
            lines.append(f"CPU: {sys_stats['cpu_percent']}% | RAM: {sys_stats['memory_percent']}%")
        return "\n".join(lines)

    def _ancestry_reload(self):
        response = self.personality.respond_to_command("ancestry reload")
        self.show_bubble_signal.emit(response)
        self.speak_signal.emit(response)

    def _toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.show_bubble_signal.emit("Paused. I'll be right here.")
        else:
            self.show_bubble_signal.emit("Back online! >|<")

    def _quit(self):
        self.show_bubble_signal.emit("Shutting down... From one another, for one another. >|<")
        QTimer.singleShot(2000, self._do_quit)

    def _do_quit(self):
        self.voice.stop_listening()
        self.browser.stop()
        self.terminal.stop_monitoring()
        self.context.stop()
        QApplication.instance().quit()

    # ==================== SYSTEM TRAY ====================

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)

        icon_paths = [
            str(Path(__file__).parent.parent / "assets" / "droid.png"),
            str(self.pip_dir / "assets" / "droid.png"),
        ]
        for path in icon_paths:
            if os.path.exists(path):
                self.tray_icon.setIcon(QIcon(path))
                break
        else:
            self.tray_icon.setIcon(QIcon.fromTheme("computer"))

        tray_menu = QMenu()

        actions = [
            ("Show Pip", self.show),
            ("Home Folder", self.home_folder.open_home),
            ("Toggle Voice", self._toggle_voice),
            ("Status", self._show_status),
            ("Quit", self._quit),
        ]

        for label, handler in actions:
            action = QAction(label, self)
            action.triggered.connect(handler)
            tray_menu.addAction(action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_activated)
        self.tray_icon.show()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
        elif reason == QSystemTrayIcon.Trigger:
            self._show_status()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Lil Arrow Pip",
            "I'm still here in the background! Double-click the tray icon to wake me.",
            QSystemTrayIcon.Information,
            3000
        )


# ==================== GLOBAL HOTKEY ====================

class HotkeyListener(QThread):
    """Global hotkey listener for voice activation."""

    activated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.is_listening = True

    def run(self):
        try:
            from pynput import keyboard

            combo = {keyboard.Key.ctrl, keyboard.Key.shift, keyboard.KeyCode.from_char('p')}
            current = set()

            def on_press(key):
                if key in combo:
                    current.add(key)
                if all(k in current for k in combo):
                    self.activated.emit()

            def on_release(key):
                current.discard(key)

            with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
                while self.is_listening:
                    listener.join(timeout=0.1)
        except:
            pass

    def stop(self):
        self.is_listening = False
