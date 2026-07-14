from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtWidgets import QWidget
from config import HIGHLIGHT_DIAMETER

class TargetHighlight(QWidget):
    """A translucent ring shown briefly around a target UI element."""

    def __init__(self, diameter: int = HIGHLIGHT_DIAMETER):
        super().__init__()
        self.diameter = diameter
        self._opacity = 0.0
        self._anim = None
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(self.diameter, self.diameter)

    def paintEvent(self, event):
        if self._opacity <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(255, 90, 90, int(255 * self._opacity)), 3)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        margin = 4
        painter.drawEllipse(margin, margin, self.diameter - 2 * margin, self.diameter - 2 * margin)

    def _get_opacity(self):
        return self._opacity

    def _set_opacity(self, value):
        self._opacity = value
        self.update()

    opacity_prop = pyqtProperty(float, _get_opacity, _set_opacity)

    def show_at(self, center_xy, hold_ms: int = 1400):
        """Positions the ring centered on (logical_x, logical_y), fades it
        in, holds, then fades it out and hides."""
        x, y = center_xy
        self.move(int(x - self.diameter / 2), int(y - self.diameter / 2))
        self.show()

        fade_in = QPropertyAnimation(self, b"opacity_prop")
        fade_in.setDuration(200)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.finished.connect(lambda: QTimer.singleShot(hold_ms, self._fade_out))
        fade_in.start()
        self._anim = fade_in

    def _fade_out(self):
        fade_out = QPropertyAnimation(self, b"opacity_prop")
        fade_out.setDuration(400)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.finished.connect(self.hide)
        fade_out.start()
        self._anim = fade_out