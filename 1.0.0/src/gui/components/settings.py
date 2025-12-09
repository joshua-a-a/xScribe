from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class SettingsComponent(QWidget):
    # Signals for configuration changes
    model_changed = Signal(str)
    enhanced_preprocessing_changed = Signal(bool)
    speaker_detection_changed = Signal(bool)
    word_timestamps_changed = Signal(bool)  # New signal for timestamping
    language_changed = Signal(str)
    auto_output_changed = Signal(bool)
    output_location_change_requested = Signal()
    download_all_models_requested = Signal()  # New signal for downloading all models

    def __init__(self, parent=None):
        super().__init__(parent)
        self.output_settings = {
            "auto_output": True,
            "base_directory": "~/Desktop/xScribe Outputs",
        }
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        outer_frame = QFrame()
        outer_frame.setObjectName("settingsOuterFrame")
        outer_frame.setStyleSheet("""
            #settingsOuterFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 8px;
            }
        """)
        outer_layout = QVBoxLayout(outer_frame)
        outer_layout.setContentsMargins(10, 10, 10, 10)

        title_label = QLabel("Transcription Settings")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setStyleSheet("color: white; background: transparent;")
        outer_layout.addWidget(title_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: 2px solid #404040;
                border-radius: 6px;
            }
            QScrollBar:vertical {
                background: #2d2d2d;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #666;
            }
        """)

        settings_widget = QWidget()
        settings_widget.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: white;
            }
            QLabel {
                color: white;
            }
            QCheckBox {
                color: white;
            }
            QRadioButton {
                color: white;
            }
        """)
        settings_layout = QGridLayout(settings_widget)
        settings_layout.setVerticalSpacing(20)
        settings_layout.setHorizontalSpacing(10)
        settings_layout.setContentsMargins(15, 15, 15, 15)

        self._create_model_selection(settings_layout, row=0)

        self._create_preprocessing_options(settings_layout, row=1)

        self._create_speaker_detection(settings_layout, row=2)

        self._create_word_timestamps(settings_layout, row=3)

        self._create_language_selection(settings_layout, row=4)

        self._create_output_settings(settings_layout, row=5)

        self._create_model_download_button(settings_layout, row=6)

        scroll.setWidget(settings_widget)
        outer_layout.addWidget(scroll)
        layout.addWidget(outer_frame)

    def _create_model_selection(self, settings_layout, row):
        model_label = QLabel("Models: (Hover your mouse over each one for info!)")
        model_label.setFont(QFont("Arial", 10))
        settings_layout.addWidget(model_label, row, 0)

        self.model_group = QButtonGroup()
        model_frame = QFrame()
        model_layout = QHBoxLayout(model_frame)

        # REMOVED LARGE MODEL - 10GB VRAM requirement too high for most systems
        models = [
            ("Tiny (Fast)", "tiny"),
            ("Base (Balanced)", "base"),
            ("Small (Better)", "small"),
            ("Medium (High Accuracy)", "medium"),
        ]

        model_tooltips = {
            "tiny": "Fastest processing (requires less than 1GB VRAM)\n"
            "• Good for: Quick drafts, real-time use\n"
            "• Accuracy: ~85% (decent for clean audio)\n"
            "• Best for: Previews, testing",
            "base": "Best speed/accuracy balance (requires ~1GB VRAM)\n"
            "• Good for: Most everyday transcription\n"
            "• Accuracy: ~92% (excellent for podcasts, videos)\n"
            "• Best for: General use (RECOMMENDED)",
            "small": "High quality (requires ~2GB VRAM)\n"
            "• Good for: Production work, clean audio\n"
            "• Accuracy: ~95% (professional grade)\n"
            "• Best for: Final transcripts, good audio quality",
            "medium": "Maximum accuracy for this version (requires ~5GB VRAM)\n"
            "• Good for: Difficult audio, technical content\n"
            "• Accuracy: ~97% (near-perfect on good audio)\n"
            "• Best for: Low bitrate, accents, multiple speakers, final production",
        }

        for i, (text, value) in enumerate(models):
            radio = QRadioButton(text)
            radio.value = value
            radio.setToolTip(model_tooltips[value])
            if value == "base":  # Default selection
                radio.setChecked(True)
            radio.toggled.connect(
                lambda checked, v=value: self.model_changed.emit(v) if checked else None
            )
            self.model_group.addButton(radio, i)
            model_layout.addWidget(radio)

        settings_layout.addWidget(model_frame, row, 1, 1, 2)

    def _create_preprocessing_options(self, settings_layout, row):
        self.enhanced_cb = QCheckBox("Enhanced preprocessing (for noisy audio)")
        self.enhanced_cb.setFont(QFont("Arial", 10))
        self.enhanced_cb.setToolTip(
            "Apply additional audio preprocessing:\n"
            "- Noise reduction\n"
            "- Audio normalization\n"
            "- Dynamic range compression\n"
            "- Better results for low-quality recordings"
        )
        self.enhanced_cb.toggled.connect(self.enhanced_preprocessing_changed.emit)
        settings_layout.addWidget(self.enhanced_cb, row, 0, 1, 3)

    def _create_speaker_detection(self, settings_layout, row):
        self.speaker_detection_cb = QCheckBox(
            "Speaker identification (offline privacy-safe detection)"
        )
        self.speaker_detection_cb.setToolTip(
            "Identify different speakers using offline analysis.\n"
            "- No internet required - completely private\n"
            "- Color-coded speaker segments in results\n"
            "- Advanced diarization algorithms\n"
            "- Works with multiple speakers"
        )
        self.speaker_detection_cb.setFont(QFont("Arial", 10))
        self.speaker_detection_cb.toggled.connect(self.speaker_detection_changed.emit)
        settings_layout.addWidget(self.speaker_detection_cb, row, 0, 1, 3)

    def _create_word_timestamps(self, settings_layout, row):
        self.word_timestamps_cb = QCheckBox(
            "Word-level timestamping (Generate subtitles & frame-precise timing)"
        )
        self.word_timestamps_cb.setChecked(
            True
        )  # Default to enabled since it's our new feature
        self.word_timestamps_cb.setToolTip(
            "SUBTITLE GENERATION:\n"
            "• Frame-accurate word timing (0.01s precision)\n"
            "• Auto-generate SRT & WebVTT subtitle files\n"
            "• Perfect for video content creation\n"
            "• Slightly slower processing for maximum accuracy\n"
            "• Export subtitles directly to video editing software"
        )
        self.word_timestamps_cb.setFont(QFont("Arial", 10))
        self.word_timestamps_cb.toggled.connect(self.word_timestamps_changed.emit)
        settings_layout.addWidget(self.word_timestamps_cb, row, 0, 1, 3)

    def _create_language_selection(self, settings_layout, row):
        lang_label = QLabel("Language:")
        lang_label.setFont(QFont("Arial", 10))
        settings_layout.addWidget(lang_label, row, 0)

        self.language_combo = QComboBox()
        self.language_combo.setMinimumHeight(
            35
        )  # Increase height for better visibility
        self.language_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 10px;
                border: 2px solid #555;
                border-radius: 4px;
            }
        """)
        languages = [
            ("Auto-detect", "auto"),
            ("English", "en"),
            ("Spanish", "es"),
            ("French", "fr"),
            ("German", "de"),
            ("Italian", "it"),
            ("Portuguese", "pt"),
            ("Chinese", "zh"),
            ("Japanese", "ja"),
            ("Korean", "ko"),
        ]

        for display_name, code in languages:
            self.language_combo.addItem(display_name, code)

        self.language_combo.setCurrentText("Auto-detect")
        self.language_combo.currentTextChanged.connect(
            lambda: self.language_changed.emit(self.language_combo.currentData())
        )
        settings_layout.addWidget(self.language_combo, row, 1)

    def _create_output_settings(self, settings_layout, row):
        self.auto_output_cb = QCheckBox(
            "Auto-save to Desktop/xScribe Outputs (Encrypted and Privacy-Safe)"
        )
        self.auto_output_cb.setChecked(self.output_settings.get("auto_output", True))
        self.auto_output_cb.setFont(QFont("Arial", 10))
        self.auto_output_cb.setToolTip(
            "Secure Auto-Save Features:\n"
            "- Privacy audit logging\n"
            "- Automatic file cleanup (GDPR)\n"
            "- Encrypted temporary storage\n"
            "- Session-based organization\n"
            "- Duplicate file protection"
        )
        self.auto_output_cb.toggled.connect(self._on_auto_output_changed)
        settings_layout.addWidget(self.auto_output_cb, row, 0, 1, 3)

        self.output_location_btn = QPushButton("Change Output Location")
        self.output_location_btn.setFont(QFont("Arial", 9))
        self.output_location_btn.setMinimumHeight(40)
        self.output_location_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5b21b6;
            }
        """)
        self.output_location_btn.clicked.connect(
            self.output_location_change_requested.emit
        )
        self.output_location_btn.setToolTip(
            f"Current: {self.output_settings['base_directory']}"
        )
        settings_layout.addWidget(self.output_location_btn, row + 1, 1)

    def _on_auto_output_changed(self, checked):
        self.output_settings["auto_output"] = checked
        self.auto_output_changed.emit(checked)

    # Public API methods
    def get_selected_model(self):
        for button in self.model_group.buttons():
            if button.isChecked():
                return button.value
        return "base"  # Default

    def set_selected_model(self, model_name):
        for button in self.model_group.buttons():
            if button.value == model_name:
                button.setChecked(True)
                break

    def get_enhanced_preprocessing(self):
        return self.enhanced_cb.isChecked()

    def set_enhanced_preprocessing(self, enabled):
        self.enhanced_cb.setChecked(enabled)

    def get_speaker_detection(self):
        return self.speaker_detection_cb.isChecked()

    def set_speaker_detection(self, enabled):
        self.speaker_detection_cb.setChecked(enabled)

    def get_word_timestamps(self):
        return self.word_timestamps_cb.isChecked()

    def set_word_timestamps(self, enabled):
        self.word_timestamps_cb.setChecked(enabled)

    def get_selected_language(self):
        return self.language_combo.currentData()

    def set_selected_language(self, language_code):
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == language_code:
                self.language_combo.setCurrentIndex(i)
                break

    def get_auto_output(self):
        return self.auto_output_cb.isChecked()

    def set_auto_output(self, enabled):
        self.auto_output_cb.setChecked(enabled)

    def get_output_settings(self):
        return self.output_settings.copy()

    def set_output_directory(self, directory):
        self.output_settings["base_directory"] = directory
        self.output_location_btn.setToolTip(f"Current: {directory}")

    def get_configuration(self):
        return {
            "model": self.get_selected_model(),
            "enhanced_preprocessing": self.get_enhanced_preprocessing(),
            "speaker_detection": self.get_speaker_detection(),
            "word_timestamps": self.get_word_timestamps(),
            "language": self.get_selected_language(),
            "auto_output": self.get_auto_output(),
            "output_directory": self.output_settings["base_directory"],
        }

    def _create_model_download_button(self, settings_layout, row):
        """Create button to download all models"""
        download_btn = QPushButton("📥 Download All")
        download_btn.setFont(QFont("Arial", 8))
        download_btn.setMaximumWidth(120)
        download_btn.setToolTip(
            "Download all Whisper models (tiny, base, small, medium)\n"
            "Only missing models will be downloaded.\n"
            "Total size: ~2.2 GB"
        )
        download_btn.clicked.connect(self.download_all_models_requested.emit)

        # Add to the right side of the grid
        settings_layout.addWidget(download_btn, row, 2, 1, 1)

    def set_configuration(self, config):
        if "model" in config:
            self.set_selected_model(config["model"])
        if "enhanced_preprocessing" in config:
            self.set_enhanced_preprocessing(config["enhanced_preprocessing"])
        if "speaker_detection" in config:
            self.set_speaker_detection(config["speaker_detection"])
        if "word_timestamps" in config:
            self.set_word_timestamps(config["word_timestamps"])
        if "language" in config:
            self.set_selected_language(config["language"])
        if "auto_output" in config:
            self.set_auto_output(config["auto_output"])
        if "output_directory" in config:
            self.set_output_directory(config["output_directory"])
