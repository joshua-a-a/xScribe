from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget


class ActionButtonsComponent(QWidget):
    # Signals
    transcribe_requested = Signal()
    privacy_report_requested = Signal()
    privacy_details_requested = Signal()
    clear_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)

        self.transcribe_btn = self._create_button(
            "🎤 Transcribe Audio", "#16a34a", "#15803d"
        )
        self.transcribe_btn.clicked.connect(self.transcribe_requested.emit)

        self.privacy_report_btn = self._create_button(
            "📊 Privacy Report", "#8b5cf6", "#7c3aed"
        )
        self.privacy_report_btn.clicked.connect(self.privacy_report_requested.emit)
        self.privacy_report_btn.setToolTip(
            "Generate comprehensive privacy compliance report\n"
            "Shows network activity, data storage, and compliance status"
        )

        self.privacy_details_btn = self._create_button(
            "Privacy Info", "#10b981", "#059669"
        )
        self.privacy_details_btn.clicked.connect(self.privacy_details_requested.emit)
        self.privacy_details_btn.setToolTip(
            "View detailed privacy features and guarantees. "
            "100% offline processing with zero data collection and local AI"
        )

        self.clear_btn = self._create_button("🗑️ Clear Results", "#dc2626", "#b91c1c")
        self.clear_btn.clicked.connect(self.clear_requested.emit)

        layout.addWidget(self.transcribe_btn)
        layout.addWidget(self.privacy_report_btn)
        layout.addWidget(self.privacy_details_btn)
        layout.addWidget(self.clear_btn)

    def _create_button(self, text, bg_color, hover_color):
        button = QPushButton(text)
        button.setMinimumHeight(45)
        button.setFont(QFont("Arial", 12, QFont.Bold))
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:disabled {{
                background-color: #d1d5db;
                color: #9ca3af;
            }}
        """)
        return button

    def set_transcribe_enabled(self, enabled):
        self.transcribe_btn.setEnabled(enabled)

    def set_all_enabled(self, enabled):
        self.transcribe_btn.setEnabled(enabled)
        self.privacy_report_btn.setEnabled(enabled)
        self.privacy_details_btn.setEnabled(enabled)
        self.clear_btn.setEnabled(enabled)
