from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu

from config import ICON_COLOR, MAX_UPLOAD_DIMENSION, MAX_UPLOAD_DIMENSION_OPTIONS

def _make_tray_icon() -> QIcon:
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(ICON_COLOR))
    painter.setPen(QColor(255, 255, 255, 200))
    painter.drawEllipse(4, 4, size - 8, size - 8)
    painter.end()
    return QIcon(pixmap)


class AssistantTray(QObject):
    toggle_tracking_requested = pyqtSignal(bool)   
    max_dimension_changed = pyqtSignal(int)       
    quit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tray = QSystemTrayIcon(_make_tray_icon(), parent)
        self.tray.setToolTip("Desktop Assistant")

        self.menu = QMenu()

        self.pause_action = QAction("Pause hotkey", checkable=True)
        self.pause_action.toggled.connect(self.toggle_tracking_requested.emit)
        self.menu.addAction(self.pause_action)

        quality_menu = self.menu.addMenu("Screenshot quality")
        self._quality_actions = []
        for dim in MAX_UPLOAD_DIMENSION_OPTIONS:
            action = QAction(f"{dim}px (longest side)", checkable=True)
            action.setChecked(dim == MAX_UPLOAD_DIMENSION)
            action.triggered.connect(lambda checked, d=dim, a=action: self._on_quality(d, a))
            quality_menu.addAction(action)
            self._quality_actions.append(action)

        self.menu.addSeparator()
        quit_action = QAction("Quit")
        quit_action.triggered.connect(self.quit_requested.emit)
        self.menu.addAction(quit_action)

        self.tray.setContextMenu(self.menu)

    def _on_quality(self, dim, chosen_action):
        for action in self._quality_actions:
            action.setChecked(action is chosen_action)
        self.max_dimension_changed.emit(dim)

    def show(self):
        self.tray.show()