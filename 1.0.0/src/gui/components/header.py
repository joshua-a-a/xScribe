from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class HeaderComponent(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main header frame
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, 
                           stop: 0 #2563eb, stop: 1 #1d4ed8);
                border-radius: 8px;
                margin: 5px;
                padding: 20px;
            }
        """)

        header_layout = QHBoxLayout(header_frame)
        header_layout.setSpacing(20)
        header_layout.setContentsMargins(15, 15, 15, 15)

        # Title and subtitle
        title_label = QLabel("xScribe- 100% Local and Private")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setWordWrap(False)

        # Add to layout
        header_layout.addWidget(title_label, 1)
        header_layout.addStretch()

        layout.addWidget(header_frame)
