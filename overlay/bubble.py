import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QApplication

class InteractiveBubble(QWidget):
    def __init__(self, submit_callback):
        super().__init__()
        self.submit_callback = submit_callback
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
                border: 1px solid #007ACC;
                border-radius: 8px;
                color: #FFFFFF;
            }
            QLineEdit {
                background-color: #2D2D2D;
                border: 1px solid #3C3C3C;
                border-radius: 4px;
                padding: 4px 8px;
                color: #FFFFFF;
            }
            QLabel {
                border: none;
                font-size: 13px;
            }
        """)

        layout = QVBoxLayout(self)
        
        self.response_label = QLabel("Listening... Type your query:")
        self.response_label.setWordWrap(True)
        layout.addWidget(self.response_label)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask about this area...")
        self.input_field.returnPressed.connect(self._on_submit)
        layout.addWidget(self.input_field)

        self.setFixedSize(300, 120)

    def activate_input(self):
        self.input_field.show()
        self.input_field.clear()
        self.response_label.setText("Listening... Type your query:")
        
        self.show()
        self.raise_()
        self.activateWindow()
        
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.user32.SetForegroundWindow(int(self.winId()))
            
        self.input_field.setFocus()

    def _on_submit(self):
        text = self.input_field.text().strip()
        if text:
            self.input_field.hide()
            self.response_label.setText("Thinking...")
            self.adjustSize()
            self.submit_callback(text)

    def set_answer(self, text: str):
        self.response_label.setText(text)
        self.adjustSize()

    def position_near_icon(self, icon_x: int, icon_y: int):
        screen = QApplication.primaryScreen()
        dpr = screen.devicePixelRatio() if screen else 1.0

        logical_x = int(icon_x / dpr)
        logical_y = int(icon_y / dpr)

        self.move(logical_x + 60, logical_y)