import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

logger = logging.getLogger(__name__)


class WelcomeDialog(QDialog):
    model_selected = Signal(str)  # Emits selected model name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_model = "base"  # Default
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Welcome to xScribe")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        layout = QVBoxLayout()
        layout.setSpacing(20)

        title = QLabel("Welcome to xScribe")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Professional Audio & Video Transcription")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666;")
        layout.addWidget(subtitle)

        features_group = QGroupBox("Features")
        features_layout = QVBoxLayout()

        features = [
            "✓ Transcribe audio and video files",
            "✓ 100% offline - complete privacy",
            "✓ Speaker identification",
            "✓ Word-level timestamps",
            "✓ Support for 21 video formats",
        ]

        for feature in features:
            label = QLabel(feature)
            label.setFont(QFont("Arial", 11))
            features_layout.addWidget(label)

        features_group.setLayout(features_layout)
        layout.addWidget(features_group)

        model_group = QGroupBox("Choose AI Model (Downloaded on first use)")
        model_layout = QVBoxLayout()

        model_info = QLabel(
            "Select a model to download. You can download additional models later."
        )
        model_info.setWordWrap(True)
        model_info.setFont(QFont("Arial", 10))
        model_layout.addWidget(model_info)

        self.model_buttons = QButtonGroup()

        models = [
            ("tiny", "Tiny - Fastest, testing (75 MB)", False),
            ("base", "Base - Recommended for most users (150 MB)", True),
            ("small", "Small - Better accuracy (500 MB)", False),
            ("medium", "Medium - High accuracy (1.5 GB)", False),
            ("all", "Download All Models - Complete collection (2.2 GB total)", False),
        ]

        for model_id, description, is_default in models:
            radio = QRadioButton(description)
            radio.setFont(QFont("Arial", 10))
            if is_default:
                radio.setChecked(True)
                radio.setStyleSheet("font-weight: bold;")
            if model_id == "all":
                radio.setStyleSheet("color: #2563eb; font-weight: bold;")
            radio.toggled.connect(
                lambda checked, m=model_id: self._on_model_selected(m)
                if checked
                else None
            )
            self.model_buttons.addButton(radio)
            model_layout.addWidget(radio)

        all_note = QLabel(
            "Tip: Download all models if you want maximum flexibility and don't mind the wait. "
            "You can always download additional models later."
        )
        all_note.setWordWrap(True)
        all_note.setFont(QFont("Arial", 9))
        all_note.setStyleSheet("color: #666; padding: 5px; margin-top: 5px;")
        model_layout.addWidget(all_note)

        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        privacy_label = QLabel(
            "🔒 Privacy First: All processing happens on your Mac. "
            "No data is ever sent to external servers."
        )
        privacy_label.setWordWrap(True)
        privacy_label.setFont(QFont("Arial", 9))
        privacy_label.setStyleSheet(
            "color: #059669; padding: 10px; background-color: #f0fdf4; border-radius: 5px;"
        )
        layout.addWidget(privacy_label)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.continue_btn = QPushButton("Continue")
        self.continue_btn.setFont(QFont("Arial", 11))
        self.continue_btn.setMinimumWidth(120)
        self.continue_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        self.continue_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.continue_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _on_model_selected(self, model_name: str):
        self.selected_model = model_name
        logger.info(f"User selected model: {model_name}")

    def get_selected_model(self) -> str:
        return self.selected_model


class ModelDownloadDialog(QDialog):
    def __init__(self, model_name: str, model_size: str, parent=None, is_batch=False):
        super().__init__(parent)
        self.model_name = model_name
        self.model_size = model_size
        self.is_batch = is_batch  # True if downloading multiple models
        self.setup_ui()

    def update_progress(
        self, message: str, percent: int, current: int = 1, total: int = 1
    ):
        self.status_label.setText(message)
        self.progress_bar.setValue(percent)

        # Update current model indicator for batch downloads
        if self.is_batch and hasattr(self, "current_model_label"):
            self.current_model_label.setText(f"Model {current} of {total}")

        if percent >= 100:
            self.status_label.setText("Download complete!")
            self.status_label.setStyleSheet("color: #059669; font-weight: bold;")

    def setup_ui(self):
        self.setWindowTitle("Downloading Model" + ("s" if self.is_batch else ""))
        self.setModal(True)
        self.setMinimumWidth(550)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        title_text = (
            "Downloading All Models"
            if self.is_batch
            else f"Downloading {self.model_name.capitalize()} Model"
        )
        title = QLabel(title_text)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        if self.is_batch:
            info = QLabel("Total size: ~2.2 GB • This may take 5-10 minutes")
        else:
            info = QLabel(f"Size: {self.model_size}")
        info.setFont(QFont("Arial", 11))
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #666;")
        layout.addWidget(info)

        if self.is_batch:
            self.current_model_label = QLabel("")
            self.current_model_label.setFont(QFont("Arial", 10))
            self.current_model_label.setAlignment(Qt.AlignCenter)
            self.current_model_label.setStyleSheet("color: #2563eb; font-weight: bold;")
            layout.addWidget(self.current_model_label)

        self.status_label = QLabel("Preparing download...")
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        if self.is_batch:
            notice_text = (
                "All models will be saved and ready for instant use. "
                "You can cancel future launches immediately as models are cached."
            )
        else:
            notice_text = (
                "This is a one-time download. The model will be saved "
                "and used for all future transcriptions."
            )

        notice = QLabel(notice_text)
        notice.setWordWrap(True)
        notice.setFont(QFont("Arial", 9))
        notice.setStyleSheet(
            "color: #666; padding: 10px; background-color: #f9fafb; border-radius: 5px;"
        )
        layout.addWidget(notice)

        self.setLayout(layout)
