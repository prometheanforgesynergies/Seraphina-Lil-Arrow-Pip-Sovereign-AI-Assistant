#!/usr/bin/env python3
"""
Lil Arrow Pip — Voice Engine (STT + TTS)
Speak to Pip like Gemini Live. Offline-first with online fallbacks.
"""

import threading
import queue
import subprocess
import tempfile
import os
import re

try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

try:
    from pydub import AudioSegment
    from pydub.playback import play as pydub_play
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False


class VoiceEngine:
    """Voice recognition and synthesis for Lil Arrow Pip."""

    def __init__(self, on_command=None, on_speaking_start=None, on_speaking_end=None):
        self.on_command = on_command
        self.on_speaking_start = on_speaking_start
        self.on_speaking_end = on_speaking_end

        self.recognizer = None
        self.microphone = None
        self.tts_engine = None
        self.is_listening = False
        self.is_speaking = False
        self.listen_thread = None
        self.command_queue = queue.Queue()

        self.voice_rate = 175
        self.voice_volume = 0.9
        self.use_edge_tts = True

        self._init_stt()
        self._init_tts()

    def _init_stt(self):
        if HAS_SPEECH_RECOGNITION:
            try:
                self.recognizer = sr.Recognizer()
                self.recognizer.energy_threshold = 300
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 0.8
                self.microphone = sr.Microphone()
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("[Voice] STT initialized — SpeechRecognition ready")
            except Exception as e:
                print(f"[Voice] STT init warning: {e}")
        else:
            print("[Voice] STT unavailable — install SpeechRecognition + pyaudio")

    def _init_tts(self):
        if HAS_PYTTSX3:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', self.voice_rate)
                self.tts_engine.setProperty('volume', self.voice_volume)
                voices = self.tts_engine.getProperty('voices')
                for voice in voices:
                    if 'english' in voice.name.lower() or 'en-us' in voice.id.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
                print("[Voice] TTS initialized — pyttsx3 ready (offline)")
            except Exception as e:
                print(f"[Voice] TTS init warning: {e}")
        else:
            print("[Voice] TTS unavailable — install pyttsx3")

    def start_listening(self):
        if not HAS_SPEECH_RECOGNITION or self.is_listening:
            return False
        self.is_listening = True
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        print("[Voice] 🎙️ Listening started — say 'Hey Pip' or press Ctrl+Shift+P")
        return True

    def stop_listening(self):
        self.is_listening = False
        print("[Voice] Listening stopped")

    def _listen_loop(self):
        while self.is_listening:
            try:
                if not self.microphone:
                    break
                with self.microphone as source:
                    print("[Voice] 👂 Listening...")
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                text = None
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    print(f"[Voice] 🎯 Offline STT: {text}")
                except:
                    try:
                        text = self.recognizer.recognize_google(audio)
                        print(f"[Voice] 🌐 Google STT: {text}")
                    except:
                        pass
                if text:
                    self.command_queue.put(text)
                    if self.on_command:
                        self.on_command(text)
            except sr.WaitTimeoutError:
                pass
            except Exception as e:
                print(f"[Voice] Listen error: {e}")

    def listen_once(self, timeout=5) -> str:
        if not HAS_SPEECH_RECOGNITION or not self.microphone:
            return ""
        try:
            with self.microphone as source:
                print("[Voice] 🎙️ Listening for command...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=8)
            try:
                text = self.recognizer.recognize_google(audio)
                print(f"[Voice] Heard: {text}")
                return text
            except:
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    print(f"[Voice] Heard (offline): {text}")
                    return text
                except:
                    return ""
        except Exception as e:
            print(f"[Voice] Listen error: {e}")
            return ""

    def speak(self, text: str):
        if not text:
            return
        clean_text = re.sub(r'[\*_#`>|]', '', text)
        clean_text = re.sub(r':[a-z_]+:', '', clean_text)
        clean_text = re.sub(r'[🎙️👂🎯🌐⚠️🔥]', '', clean_text)
        clean_text = clean_text.strip()
        if not clean_text:
            return

        self.is_speaking = True
        if self.on_speaking_start:
            self.on_speaking_start()

        spoken = False
        if self.use_edge_tts and HAS_EDGE_TTS and HAS_PYDUB:
            spoken = self._speak_edge(clean_text)

        if not spoken and HAS_PYTTSX3 and self.tts_engine:
            self._speak_pyttsx3(clean_text)
            spoken = True

        if not spoken:
            print(f"[Voice] 🔇 (TTS unavailable) {clean_text[:80]}...")

        self.is_speaking = False
        if self.on_speaking_end:
            self.on_speaking_end()

    def _speak_pyttsx3(self, text: str):
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"[Voice] pyttsx3 error: {e}")

    def _speak_edge(self, text: str) -> bool:
        try:
            import asyncio
            async def _edge_speak():
                communicate = edge_tts.Communicate(text, voice="en-US-AriaNeural")
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    tmp_path = tmp.name
                    await communicate.save(tmp_path)
                audio = AudioSegment.from_mp3(tmp_path)
                pydub_play(audio)
                os.unlink(tmp_path)
            asyncio.run(_edge_speak())
            return True
        except Exception as e:
            print(f"[Voice] Edge TTS failed, falling back: {e}")
            return False

    def stop_speaking(self):
        if HAS_PYTTSX3 and self.tts_engine:
            try:
                self.tts_engine.stop()
            except:
                pass
        self.is_speaking = False

    def status(self) -> dict:
        return {
            "stt_available": HAS_SPEECH_RECOGNITION and self.recognizer is not None,
            "tts_available": HAS_PYTTSX3 or (HAS_EDGE_TTS and HAS_PYDUB),
            "is_listening": self.is_listening,
            "is_speaking": self.is_speaking,
        }
