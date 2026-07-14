import sys

from PyQt6.QtCore import QTimer, QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication

from overlay.icon import FloatingIcon
from overlay.bubble import InteractiveBubble
from overlay.highlight import TargetHighlight
from overlay.tray import AssistantTray
from input.hotkey import HotkeyListener
from input.cursor import get_cursor_position
from capture.screenshot import capture_full_screen, prepare_for_upload
from brain.client import query_vision_llm
from brain.coords import bbox_to_screen
from config import (
    MAX_UPLOAD_DIMENSION,
    HISTORY_LIMIT,
    GLIDE_DURATION_MS,
    HIGHLIGHT_HOLD_MS,
    RETURN_HOLD_MS,
)

class WorkerThread(QThread):
    finished = pyqtSignal(str, dict)  

    def __init__(self, image, query, history):
        super().__init__()
        self.image = image
        self.query = query
        self.history = history

    def run(self):
        result = query_vision_llm(self.image, self.query, self.history)
        self.finished.emit(self.query, result)

class AssistantApp:
    def __init__(self):
        self.app = QApplication(sys.argv)

        self.icon = FloatingIcon()
        self.bubble = None
        self.highlight = TargetHighlight()

        self.captured_image = None
        self.screen_origin = None     
        self.screen_size = None        
        self.current_bbox = None

        self.history = []
        self.tracking_paused = False
        self.max_dimension = MAX_UPLOAD_DIMENSION

        self.hotkey_listener = HotkeyListener()
        self.hotkey_listener.triggered.connect(self.on_trigger)

        self.track_timer = QTimer()
        self.track_timer.setInterval(16)
        self.track_timer.timeout.connect(self.update_positions)

        self.return_timer = QTimer()
        self.return_timer.setSingleShot(True)
        self.return_timer.timeout.connect(self._return_to_cursor)

        self.tray = AssistantTray()
        self.tray.toggle_tracking_requested.connect(self.set_tracking_paused)
        self.tray.max_dimension_changed.connect(self.set_max_dimension)
        self.tray.quit_requested.connect(self.app.quit)

    def start(self):
        self.hotkey_listener.start()
        self.icon.show()
        self.track_timer.start()
        self.tray.show()
        sys.exit(self.app.exec())

    def set_tracking_paused(self, paused: bool):
        self.tracking_paused = paused
        if paused:
            self.hotkey_listener.stop()
        else:
            self.hotkey_listener.start()

    def set_max_dimension(self, dim: int):
        self.max_dimension = dim

    def update_positions(self):
        if self.tracking_paused:
            return
        x, y = get_cursor_position()
        if self.icon.isVisible():
            self.icon.position_near_cursor(x, y)
        if self.bubble and self.bubble.isVisible():
            self.bubble.position_near_icon(x, y)

    def _dpr(self):
        screen = QApplication.primaryScreen()
        return screen.devicePixelRatio() if screen else 1.0

    def on_trigger(self):
        self.return_timer.stop()
        if not self.track_timer.isActive():
            self.track_timer.start()

        x, y = get_cursor_position()
        dpr = self._dpr()
        cursor_phys = (int(x * dpr), int(y * dpr))

        full_image, self.screen_origin, self.screen_size = capture_full_screen()
        self.captured_image = prepare_for_upload(
            full_image, cursor_phys, self.screen_origin, self.max_dimension
        )

        if self.bubble is None:
            self.bubble = InteractiveBubble(self.process_query)

        self.bubble.position_near_icon(x, y)
        QTimer.singleShot(50, self.bubble.activate_input)

    def process_query(self, query: str):
        if self.captured_image:
            self.worker = WorkerThread(self.captured_image, query, self.history)
            self.worker.finished.connect(self.handle_response)
            self.worker.start()

    # --- response handling, context, and guiding the user ---
    def handle_response(self, query: str, response: dict):
        answer = response.get("answer", "No answer generated.")
        self.current_bbox = response.get("bbox")

        self.history.append({"query": query, "answer": answer})
        self.history = self.history[-HISTORY_LIMIT:]

        if self.bubble:
            self.bubble.set_answer(answer)

        target = self._resolve_target()
        if target:
            self.track_timer.stop()
            self.return_timer.stop()
            self.icon.glide_to(target, duration_ms=GLIDE_DURATION_MS, on_finished=self._on_glide_finished)
            self.highlight.show_at(target, hold_ms=HIGHLIGHT_HOLD_MS)

    def _resolve_target(self):
        if not self.current_bbox or not self.screen_origin:
            return None
        return bbox_to_screen(self.current_bbox, self.screen_origin, self.screen_size, self._dpr())

    def _on_glide_finished(self):
        self.return_timer.setInterval(RETURN_HOLD_MS)
        self.return_timer.start()

    def _return_to_cursor(self):
        x, y = get_cursor_position()
        dpr = self._dpr()
        logical_x = int(x / dpr) + 12   
        logical_y = int(y / dpr) + 12
        self.icon.glide_to((logical_x, logical_y), duration_ms=GLIDE_DURATION_MS, on_finished=self._resume_tracking)

    def _resume_tracking(self):
        self.track_timer.start()


if __name__ == "__main__":
    assistant = AssistantApp()
    assistant.start()