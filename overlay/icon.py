from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtWidgets import QWidget, QApplication
from config import ICON_SIZE, ICON_IMAGE_PATH

class FloatingIcon(QWidget):
    def __init__(self):
        super().__init__()
        self._anim = None
        self._pixmap = self._load_pixmap()
        self.init_ui()

    def _load_pixmap(self) -> QPixmap:
        pixmap = QPixmap(ICON_IMAGE_PATH)
        if pixmap.isNull():
            print(f"[FloatingIcon] Could not load icon image at '{ICON_IMAGE_PATH}'")
            blank = QPixmap(ICON_SIZE, ICON_SIZE)
            blank.fill(Qt.GlobalColor.transparent)
            return blank
        return pixmap.scaled(
            ICON_SIZE,
            ICON_SIZE,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(ICON_SIZE, ICON_SIZE)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        x = (ICON_SIZE - self._pixmap.width()) // 2
        y = (ICON_SIZE - self._pixmap.height()) // 2
        painter.drawPixmap(x, y, self._pixmap)

    def position_near_cursor(self, cursor_x: int, cursor_y: int):
        screen = QApplication.primaryScreen()
        dpr = screen.devicePixelRatio() if screen else 1.0

        logical_x = int(cursor_x / dpr)
        logical_y = int(cursor_y / dpr)

        offset = 12
        self.move(logical_x + offset, logical_y + offset)

    def _get_pos(self):
        return self.pos()

    def _set_pos(self, point: QPoint):
        self.move(point)

    pos_prop = pyqtProperty(QPoint, _get_pos, _set_pos)

    def glide_to(self, target_xy, duration_ms: int = 400, on_finished=None):
        target = QPoint(*target_xy)
        anim = QPropertyAnimation(self, b"pos_prop")
        anim.setDuration(duration_ms)
        anim.setStartValue(self.pos())
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        if on_finished:
            anim.finished.connect(on_finished)
        anim.start()
        self._anim = anim