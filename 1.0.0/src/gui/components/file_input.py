import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class FileInputComponent(QWidget):
    # Signals for parent communication
    file_selected = Signal(str)  # Emits file path when file is selected

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        mode_tabs = QTabWidget()

        single_tab = QWidget()
        self._setup_single_file_ui(single_tab)
        mode_tabs.addTab(single_tab, "Single File")

        self.batch_component = BatchInputComponent()
        mode_tabs.addTab(self.batch_component, "Batch Processing")

        layout.addWidget(mode_tabs)

    def _setup_single_file_ui(self, parent_widget):
        layout = QVBoxLayout(parent_widget)

        file_group = QGroupBox("Audio File Selection")
        file_group.setFont(QFont("Arial", 12, QFont.Bold))
        file_group.setMinimumHeight(220)  # Consistent sizing
        file_layout = QVBoxLayout(file_group)

        self.drop_area = DropZoneLabel()
        self.drop_area.setMinimumHeight(150)  # Larger drop zone
        self.drop_area.setAlignment(Qt.AlignCenter)
        self.drop_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #cbd5e1;
                border-radius: 8px;
                background-color: rgba(248, 250, 252, 0.8);
                color: #64748b;
                font-size: 14px;
                padding: 20px;
            }
            QLabel:hover {
                border-color: #2563eb;
                background-color: rgba(239, 246, 255, 0.8);
                color: #1e40af;
            }
        """)
        drop_prompt = (
            "Drag and Drop Audio or Video Files Here or click Browse Files below\n\n"
            "Supported Audio: MP3, WAV, M4A, FLAC, OGG, Opus\n"
            "Supported Video: MP4, MOV, AVI, MKV, WebM, and more"
        )
        self.drop_area.set_default_text(drop_prompt)

        self.drop_area.files_dropped.connect(self._handle_files_dropped)

        file_info_layout = QHBoxLayout()

        self.file_label = QLabel("No file selected")
        self.file_label.setFont(QFont("Arial", 10))
        self.file_label.setStyleSheet("color: #64748b;")

        self.browse_btn = QPushButton("Browse Files")
        self.browse_btn.setMinimumHeight(35)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        self.browse_btn.clicked.connect(self._browse_files)

        file_info_layout.addWidget(self.file_label)
        file_info_layout.addStretch()
        file_info_layout.addWidget(self.browse_btn)

        file_layout.addWidget(self.drop_area)
        file_layout.addLayout(file_info_layout)

        layout.addWidget(file_group)

    def _browse_files(self):
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio or Video File",
            "",
            "All Files (*)",
        )

        if file_path:
            self._set_selected_file(file_path)

    def _handle_files_dropped(self, file_paths):
        if file_paths:
            # Take the first file for single file mode
            self._set_selected_file(file_paths[0])

    def _set_selected_file(self, file_path):
        from pathlib import Path

        from PySide6.QtWidgets import QMessageBox

        # Validate file format first
        from src.core.audio_processor import AudioProcessor

        processor = AudioProcessor()

        if not processor.is_supported_file(file_path):
            file_ext = Path(file_path).suffix.lower()
            QMessageBox.warning(
                self,
                "Unsupported Format",
                f"The file format '{file_ext}' is not supported.\n\n"
                f"Supported audio: MP3, WAV, M4A, FLAC, OGG, Opus\n"
                f"Supported video: MP4, MOV, AVI, MKV, WebM, and 15+ more",
            )
            return

        self.current_file = file_path
        filename = os.path.basename(file_path)

        # Show if it's a video file
        if processor.is_video_file(file_path):
            self.file_label.setText(f"Selected (Video): {filename}")
        else:
            self.file_label.setText(f"Selected: {filename}")

        self.file_label.setStyleSheet("color: #059669; font-weight: bold;")
        self.file_selected.emit(file_path)

    def get_selected_file(self):
        return self.current_file

    def select_file(self, file_path):
        if file_path and os.path.isfile(file_path):
            self._set_selected_file(file_path)

    def clear_selection(self):
        self.current_file = None
        self.file_label.setText("No file selected")
        self.file_label.setStyleSheet("color: #64748b;")
        if hasattr(self, "drop_area"):
            self.drop_area.reset_display()


class BatchInputComponent(QWidget):
    # Signals
    files_changed = Signal(list)  # Emits list of files when batch changes
    batch_start_requested = Signal()
    batch_pause_requested = Signal()
    batch_stop_requested = Signal()
    export_batch_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.batch_files = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        batch_group = QGroupBox("Batch File Processing")
        batch_group.setFont(QFont("Arial", 12, QFont.Bold))
        batch_group.setMinimumHeight(220)  # Match single file at 220px
        batch_layout = QVBoxLayout(batch_group)

        batch_controls = QHBoxLayout()

        self.add_files_btn = QPushButton("Add Files")
        self.add_files_btn.setMinimumHeight(35)
        self.add_files_btn.setStyleSheet(self._get_primary_button_style())
        self.add_files_btn.clicked.connect(self._add_files)

        self.clear_batch_btn = QPushButton("Clear All")
        self.clear_batch_btn.setStyleSheet(self._get_danger_button_style())
        self.clear_batch_btn.clicked.connect(self._clear_all_files)

        batch_controls.addWidget(self.add_files_btn)
        batch_controls.addWidget(self.clear_batch_btn)
        batch_controls.addStretch()

        self.batch_file_tree = QTreeWidget()
        self.batch_file_tree.setHeaderLabels(["File", "Status", "Progress", "Size"])
        self.batch_file_tree.header().resizeSection(0, 300)
        self.batch_file_tree.header().resizeSection(1, 100)
        self.batch_file_tree.header().resizeSection(2, 100)
        self.batch_file_tree.setMinimumHeight(150)  # Match drop area

        batch_process_controls = QHBoxLayout()

        self.batch_start_btn = QPushButton("Start Batch Processing")
        self.batch_start_btn.setMinimumHeight(40)
        self.batch_start_btn.setStyleSheet(self._get_success_button_style())
        self.batch_start_btn.clicked.connect(self.batch_start_requested.emit)

        self.batch_pause_btn = QPushButton("Pause")
        self.batch_pause_btn.setEnabled(False)
        self.batch_pause_btn.setStyleSheet(self._get_warning_button_style())
        self.batch_pause_btn.clicked.connect(self.batch_pause_requested.emit)

        self.batch_stop_btn = QPushButton("Stop")
        self.batch_stop_btn.setEnabled(False)
        self.batch_stop_btn.setStyleSheet(self._get_danger_button_style())
        self.batch_stop_btn.clicked.connect(self.batch_stop_requested.emit)

        self.batch_export_btn = QPushButton("Export Batch Results")
        self.batch_export_btn.setStyleSheet(self._get_success_button_style())
        self.batch_export_btn.clicked.connect(self.export_batch_requested.emit)

        batch_process_controls.addWidget(self.batch_start_btn)
        batch_process_controls.addWidget(self.batch_pause_btn)
        batch_process_controls.addWidget(self.batch_stop_btn)
        batch_process_controls.addWidget(self.batch_export_btn)
        batch_process_controls.addStretch()

        self.batch_progress_label = QLabel("Ready for batch processing")
        self.batch_progress_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.batch_progress_label.setStyleSheet("color: #1e293b; padding: 5px;")

        self.batch_progress_bar = QProgressBar()
        self.batch_progress_bar.setMinimumHeight(30)  # Make it taller
        self.batch_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #cbd5e1;
                border-radius: 8px;
                text-align: center;
                background-color: #f1f5f9;
                font-weight: bold;
                font-size: 13px;
                color: #1e293b;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:1 #2563eb);
                border-radius: 6px;
            }
        """)
        self.batch_progress_bar.setVisible(False)

        batch_layout.addLayout(batch_controls)
        batch_layout.addWidget(self.batch_file_tree)
        batch_layout.addLayout(batch_process_controls)
        batch_layout.addWidget(self.batch_progress_label)
        batch_layout.addWidget(self.batch_progress_bar)

        layout.addWidget(batch_group)

    def _add_files(self):
        from PySide6.QtWidgets import QFileDialog

        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Audio or Video Files",
            "",
            "All Files (*)",
        )

        for file_path in file_paths:
            if file_path not in self.batch_files:
                self.batch_files.append(file_path)
                self._add_file_to_tree(file_path)

        self.files_changed.emit(self.batch_files)

    def _add_file_to_tree(self, file_path):
        filename = os.path.basename(file_path)
        try:
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            size_str = f"{size_mb:.1f} MB"
        except OSError:
            size_str = "Unknown"

        item = QTreeWidgetItem([filename, "Pending", "0%", size_str])
        item.setData(0, Qt.UserRole, file_path)  # Store full path
        self.batch_file_tree.addTopLevelItem(item)

    def add_external_files(self, file_paths):
        added_count = 0
        for file_path in file_paths:
            if file_path and file_path not in self.batch_files:
                self.batch_files.append(file_path)
                self._add_file_to_tree(file_path)
                added_count += 1

        if added_count:
            self.files_changed.emit(self.batch_files)

        return added_count

    def _clear_all_files(self):
        self.batch_files.clear()
        self.batch_file_tree.clear()
        self.files_changed.emit(self.batch_files)

    def get_batch_files(self):
        return self.batch_files.copy()

    def update_file_status(self, file_path, status, progress=None):
        for i in range(self.batch_file_tree.topLevelItemCount()):
            item = self.batch_file_tree.topLevelItem(i)
            if item.data(0, Qt.UserRole) == file_path:
                item.setText(1, status)
                if progress is not None:
                    item.setText(2, f"{progress}%")
                break

    def set_batch_controls_enabled(
        self, start_enabled, pause_enabled, stop_enabled, export_enabled=True
    ):
        self.batch_start_btn.setEnabled(start_enabled)
        self.batch_pause_btn.setEnabled(pause_enabled)
        self.batch_stop_btn.setEnabled(stop_enabled)
        self.batch_export_btn.setEnabled(export_enabled)

    def update_batch_progress(self, progress, text):
        self.batch_progress_bar.setValue(progress)
        self.batch_progress_label.setText(text)
        self.batch_progress_bar.setVisible(progress > 0)

    # Button styles
    def _get_primary_button_style(self):
        return """
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """

    def _get_success_button_style(self):
        return """
            QPushButton {
                background-color: #16a34a;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #15803d;
            }
            QPushButton:disabled {
                background-color: #d1d5db;
                color: #9ca3af;
            }
        """

    def _get_warning_button_style(self):
        return """
            QPushButton {
                background-color: #f59e0b;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d97706;
            }
            QPushButton:disabled {
                background-color: #d1d5db;
                color: #9ca3af;
            }
        """

    def _get_danger_button_style(self):
        return """
            QPushButton {
                background-color: #dc2626;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
        """


class DropZoneLabel(QLabel):
    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._default_text = ""
        self._max_preview_items = 4
        from src.core.audio_processor import AudioProcessor

        self._audio_processor = AudioProcessor()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    # Check if it's a supported file
                    if self._is_supported_file(file_path):
                        file_paths.append(file_path)

            if file_paths:
                self._show_dropped_files(file_paths)
                self.files_dropped.emit(file_paths)
                event.acceptProposedAction()
            else:
                self._show_invalid_drop_message()
                event.ignore()
        else:
            event.ignore()

    def set_default_text(self, text):
        self._default_text = text
        self.setText(text)

    def reset_display(self):
        self.setText(self._default_text)

    def _show_dropped_files(self, file_paths):
        names = [os.path.basename(path) or path for path in file_paths]
        if not names:
            self.reset_display()
            return

        if len(names) == 1:
            self.setText(f"Ready to transcribe:\n• {names[0]}")
            return

        preview = "\n".join(f"• {name}" for name in names[: self._max_preview_items])
        remaining = len(names) - self._max_preview_items
        if remaining > 0:
            preview += f"\n(+{remaining} more)"

        self.setText(
            "Files detected:\n"
            f"{preview}\n\n"
            "First file will be queued for single transcription."
        )

    def _show_invalid_drop_message(self):
        self.setText(
            "No supported audio or video files detected.\n"
            "Please drop MP3, WAV, MP4, MOV, or other supported formats."
        )

    def _is_supported_file(self, file_path):
        return self._audio_processor.is_supported_file(file_path)
