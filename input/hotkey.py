from PyQt6.QtCore import QObject, pyqtSignal
from pynput import keyboard
from config import ACTIVATION_HOTKEY


class HotkeyListener(QObject):
    triggered = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._listener = None

    def start(self):
        hotkey_dict = {ACTIVATION_HOTKEY: self._on_hotkey_pressed}
        self._listener = keyboard.GlobalHotKeys(hotkey_dict)
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()

    def _on_hotkey_pressed(self):
        self.triggered.emit()