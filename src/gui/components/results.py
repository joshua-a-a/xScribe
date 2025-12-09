from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ResultsComponent(QWidget):
    # Signals
    export_requested = Signal(str)  # Export format requested
    timestamp_settings_changed = Signal(bool, str)  # Show timestamps, interval

    def __init__(self, parent=None):
        super().__init__(parent)
        self.speaker_colors = {}
        self.current_results = None
        self.transcription_result = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        results_group = QGroupBox("Transcription Results")
        results_group.setFont(QFont("Arial", 12, QFont.Bold))
        results_layout = QVBoxLayout(results_group)

        # Create tab widget
        self.results_tabs = QTabWidget()

        # Basic results tab
        self._create_basic_results_tab()

        # Timestamped results tab
        self._create_timestamped_results_tab()

        # Subtitle generation tab
        self._create_subtitle_tab()

        results_layout.addWidget(self.results_tabs)
        layout.addWidget(results_group)

    def _create_basic_results_tab(self):
        basic_widget = QWidget()
        basic_layout = QVBoxLayout(basic_widget)

        # Spacer keeps tab height aligned with other tabs
        control_spacer = QFrame()
        control_spacer.setFixedHeight(40)  # Match height of controls in other tabs
        basic_layout.addWidget(control_spacer)

        self.basic_results_text = QTextEdit()
        self.basic_results_text.setReadOnly(True)
        self.basic_results_text.setMinimumHeight(300)  # Consistent size across all tabs
        self.basic_results_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.4;
                padding: 8px;
            }
        """)
        self.basic_results_text.setPlaceholderText(
            "Basic results preview will appear here after transcription with respective settings are enabled...\n\n"
            "If you just want very quick and basic results, transcribe with tiny/base model and normal settings."
        )
        basic_layout.addWidget(self.basic_results_text)

        self.results_tabs.addTab(basic_widget, "Basic Results")

    def _create_subtitle_tab(self):
        """Create the subtitle tab with SRT/VTT format preview."""
        subtitle_widget = QWidget()
        subtitle_layout = QVBoxLayout(subtitle_widget)

        # Subtitle format controls
        format_controls = QFrame()
        format_controls.setFixedHeight(40)  # Fixed height for alignment
        format_layout = QHBoxLayout(format_controls)
        format_layout.setContentsMargins(
            0, 0, 0, 0
        )  # Remove margins for consistent height

        format_label = QLabel("Subtitle Format:")
        format_label.setStyleSheet("font-weight: bold; color: #555;")
        self.subtitle_format_combo = QComboBox()
        self.subtitle_format_combo.addItems(["SRT", "VTT"])
        self.subtitle_format_combo.setMinimumWidth(100)  # Make wider to show full text
        self.subtitle_format_combo.currentTextChanged.connect(
            self._update_subtitle_preview
        )

        format_layout.addWidget(format_label)
        format_layout.addWidget(self.subtitle_format_combo)
        format_layout.addStretch()
        subtitle_layout.addWidget(format_controls)

        # Subtitle preview
        self.subtitle_preview = QTextEdit()
        self.subtitle_preview.setReadOnly(True)
        self.subtitle_preview.setMinimumHeight(300)  # Consistent size across all tabs
        self.subtitle_preview.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.4;
                padding: 8px;
            }
        """)
        self.subtitle_preview.setPlaceholderText(
            "Subtitle preview will appear here after transcription with word timestamps enabled..."
        )
        subtitle_layout.addWidget(self.subtitle_preview)

        self.results_tabs.addTab(subtitle_widget, "Subtitles")

    def _update_subtitle_preview(self):
        """Update subtitle preview based on selected format."""
        if not hasattr(self, "transcription_result") or not self.transcription_result:
            return

        try:
            format_type = self.subtitle_format_combo.currentText()

            if format_type == "SRT":
                subtitle_content = self._generate_srt_content()
            else:  # VTT
                subtitle_content = self._generate_vtt_content()

            self.subtitle_preview.setPlainText(subtitle_content)
        except Exception as e:
            self.subtitle_preview.setPlainText(
                f"Error generating subtitle preview: {str(e)}"
            )

    def _generate_srt_content(self):
        """Generate SRT format subtitle content."""
        if not hasattr(
            self, "transcription_result"
        ) or not self.transcription_result.get("segments"):
            return "No word-level timestamps available. Enable word timestamps in settings to generate subtitles."

        srt_content = []
        for i, segment in enumerate(self.transcription_result["segments"], 1):
            start_time = self._format_time_srt(segment.get("start", 0))
            end_time = self._format_time_srt(segment.get("end", 0))
            text = segment.get("text", "").strip()

            if text:
                srt_content.append(f"{i}")
                srt_content.append(f"{start_time} --> {end_time}")
                srt_content.append(text)
                srt_content.append("")  # Empty line between entries

        return "\n".join(srt_content)

    def _generate_vtt_content(self):
        """Generate WebVTT format subtitle content."""
        if not hasattr(
            self, "transcription_result"
        ) or not self.transcription_result.get("segments"):
            return "No word-level timestamps available. Enable word timestamps in settings to generate subtitles."

        vtt_content = ["WEBVTT", "", "NOTE", "Generated by xScribe", ""]

        for segment in self.transcription_result["segments"]:
            start_time = self._format_time_vtt(segment.get("start", 0))
            end_time = self._format_time_vtt(segment.get("end", 0))
            text = segment.get("text", "").strip()

            if text:
                vtt_content.append(f"{start_time} --> {end_time}")
                vtt_content.append(text)
                vtt_content.append("")  # Empty line between entries

        return "\n".join(vtt_content)

    def _format_time_srt(self, seconds):
        """Format time for SRT format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

    def _format_time_vtt(self, seconds):
        """Format time for VTT format (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"

    def _create_timestamped_results_tab(self):
        """Create timestamped results tab with controls"""
        timestamp_widget = QWidget()
        timestamp_layout = QVBoxLayout(timestamp_widget)

        # Timestamp controls
        timestamp_controls = self._create_timestamp_controls()
        timestamp_layout.addWidget(timestamp_controls)

        # Speaker legend frame (initially hidden)
        self.speaker_legend_frame = QFrame()
        self.speaker_legend_layout = QHBoxLayout(self.speaker_legend_frame)
        self.speaker_legend_frame.setVisible(False)
        timestamp_layout.addWidget(self.speaker_legend_frame)

        # Timestamped text area
        self.timestamp_text = QTextEdit()
        self.timestamp_text.setReadOnly(True)
        self.timestamp_text.setMinimumHeight(300)  # Consistent size across all tabs
        self.timestamp_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.4;
                padding: 8px;
            }
        """)
        self.timestamp_text.setPlaceholderText(
            "Timestamped preview will appear here after transcription with respective settings are enabled...\n\n"
            "If you just want very quick and basic results, transcribe with tiny/base model and normal settings."
        )
        timestamp_layout.addWidget(self.timestamp_text)

        self.results_tabs.addTab(timestamp_widget, "Timestamped")

    def _create_timestamp_controls(self):
        """Create timestamp control panel"""
        timestamp_controls = QFrame()
        timestamp_controls.setFixedHeight(40)  # Fixed height for alignment
        controls_layout = QHBoxLayout(timestamp_controls)
        controls_layout.setContentsMargins(
            0, 0, 0, 0
        )  # Remove margins for consistent height

        # Show timestamps checkbox
        self.show_timestamps_cb = QCheckBox("Show timestamps")
        self.show_timestamps_cb.setChecked(True)
        self.show_timestamps_cb.toggled.connect(self._on_timestamp_settings_changed)

        # Timestamp interval
        interval_label = QLabel("Interval:")
        self.timestamp_interval_combo = QComboBox()
        self.timestamp_interval_combo.addItems(["10s", "30s", "60s", "Auto"])
        self.timestamp_interval_combo.setCurrentText("30s")
        self.timestamp_interval_combo.setMinimumWidth(
            100
        )  # Make wider to show full text
        self.timestamp_interval_combo.currentTextChanged.connect(
            self._on_timestamp_settings_changed
        )

        # Export button
        self.export_btn = QPushButton("Export (TXT/SRT/VTT/DOCX/JSON)")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #047857;
            }
        """)
        self.export_btn.clicked.connect(self._show_export_dialog)

        controls_layout.addWidget(self.show_timestamps_cb)
        controls_layout.addWidget(interval_label)
        controls_layout.addWidget(self.timestamp_interval_combo)
        controls_layout.addStretch()
        controls_layout.addWidget(self.export_btn)

        return timestamp_controls

    def _on_timestamp_settings_changed(self):
        """Handle timestamp settings change"""
        show_timestamps = self.show_timestamps_cb.isChecked()
        interval = self.timestamp_interval_combo.currentText()
        self.timestamp_settings_changed.emit(show_timestamps, interval)

        # Re-format current results if available
        if self.current_results:
            self._update_timestamped_display()

    def _show_export_dialog(self):
        """Show export format selection dialog"""
        from PySide6.QtWidgets import (
            QButtonGroup,
            QDialog,
            QHBoxLayout,
            QPushButton,
            QRadioButton,
            QVBoxLayout,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Export Format")
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)

        # Export format selection
        format_group = QButtonGroup()
        formats = [
            ("Plain Text (.txt)", "txt"),
            ("SubRip Subtitles (.srt)", "srt"),
            ("WebVTT Subtitles (.vtt)", "vtt"),
            ("Word Document (.docx)", "docx"),
            ("JSON Data (.json)", "json"),
        ]

        for display_name, format_code in formats:
            radio = QRadioButton(display_name)
            radio.format_code = format_code
            if format_code == "txt":
                radio.setChecked(True)
            format_group.addButton(radio)
            layout.addWidget(radio)

        # Dialog buttons
        button_layout = QHBoxLayout()
        export_btn = QPushButton("Export")
        cancel_btn = QPushButton("Cancel")

        export_btn.clicked.connect(
            lambda: self._handle_export_selection(dialog, format_group)
        )
        cancel_btn.clicked.connect(dialog.reject)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(export_btn)
        layout.addLayout(button_layout)

        dialog.exec()

    def _handle_export_selection(self, dialog, format_group):
        """Handle export format selection"""
        for button in format_group.buttons():
            if button.isChecked():
                self.export_requested.emit(button.format_code)
                dialog.accept()
                break

    def set_basic_results(self, text):
        """Set basic results text"""
        self.basic_results_text.setPlainText(text)

    def set_transcription_results(self, results):
        """Set full transcription results"""
        from src.models.transcription_result import TranscriptionResult

        if isinstance(results, TranscriptionResult):
            self.current_results = results
            self.transcription_result = (
                results.to_dict()
                if hasattr(results, "to_dict")
                else {
                    "segments": [
                        seg.__dict__ if hasattr(seg, "__dict__") else seg
                        for seg in results.segments
                    ]
                    if results.segments
                    else []
                }
            )

            # Update basic results
            self.set_basic_results(results.full_text)

            # Update timestamped results
            self._update_timestamped_display()

            # Update subtitle preview
            self._update_subtitle_preview()

            # Update speaker legend if speakers detected
            if results.segments and any(seg.speaker for seg in results.segments):
                self._update_speaker_legend(results.segments)
        else:
            # Handle plain text results
            self.set_basic_results(str(results))
            self.current_results = None
            self.transcription_result = None

    def _update_timestamped_display(self):
        """Update the timestamped results display"""
        if not self.current_results or not self.current_results.segments:
            return

        show_timestamps = self.show_timestamps_cb.isChecked()
        interval = self.timestamp_interval_combo.currentText()

        # Format timestamped text
        formatted_text = self._format_timestamped_text(
            self.current_results.segments,
            show_timestamps=show_timestamps,
            interval=interval,
        )

        self.timestamp_text.setHtml(formatted_text)

    def _format_timestamped_text(self, segments, show_timestamps=True, interval="30s"):
        """Format segments into timestamped HTML text with speaker colors"""
        if not segments:
            return ""

        html_parts = []
        html_parts.append(
            '<div style="font-family: Monaco, monospace; font-size: 10pt;">'
        )

        for segment in segments:
            # Create timestamp if needed
            timestamp_str = ""
            if show_timestamps and segment.start is not None:
                minutes, seconds = divmod(int(segment.start), 60)
                timestamp_str = f'<span style="color: #6b7280; font-weight: bold;">[{minutes:02d}:{seconds:02d}]</span> '

            # Get speaker color if speaker identification is available
            speaker_str = ""
            text_color = "black"
            if segment.speaker:
                speaker_color = self._get_speaker_color(segment.speaker)
                text_color = speaker_color
                speaker_str = f'<span style="color: {speaker_color}; font-weight: bold;">{segment.speaker}:</span> '

            # Format the complete segment
            segment_html = f'<p>{timestamp_str}{speaker_str}<span style="color: {text_color};">{segment.text}</span></p>'
            html_parts.append(segment_html)

        html_parts.append("</div>")
        return "".join(html_parts)

    def _get_speaker_color(self, speaker):
        """Get consistent color for a speaker"""
        if speaker not in self.speaker_colors:
            # Assign colors in rotation
            colors = ["#e11d48", "#2563eb", "#16a34a", "#f59e0b", "#8b5cf6", "#06b6d4"]
            self.speaker_colors[speaker] = colors[
                len(self.speaker_colors) % len(colors)
            ]
        return self.speaker_colors[speaker]

    def _update_speaker_legend(self, segments):
        """Update the speaker legend display"""
        # Clear existing legend
        for i in reversed(range(self.speaker_legend_layout.count())):
            child = self.speaker_legend_layout.itemAt(i).widget()
            if child:
                child.deleteLater()

        # Find unique speakers
        speakers = set()
        for segment in segments:
            if segment.speaker:
                speakers.add(segment.speaker)

        if not speakers:
            self.speaker_legend_frame.setVisible(False)
            return

        # Create legend
        legend_label = QLabel("Speakers:")
        legend_label.setFont(QFont("Arial", 9, QFont.Bold))
        self.speaker_legend_layout.addWidget(legend_label)

        for speaker in sorted(speakers):
            color = self._get_speaker_color(speaker)
            speaker_label = QLabel(speaker)
            speaker_label.setStyleSheet(f"""
                color: {color};
                font-weight: bold;
                background-color: rgba({self._hex_to_rgb(color)}, 0.1);
                padding: 2px 8px;
                border-radius: 4px;
                margin: 2px;
            """)
            self.speaker_legend_layout.addWidget(speaker_label)

        self.speaker_legend_layout.addStretch()
        self.speaker_legend_frame.setVisible(True)

    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB values"""
        hex_color = hex_color.lstrip("#")
        return ", ".join(str(int(hex_color[i : i + 2], 16)) for i in (0, 2, 4))

    def clear_results(self):
        """Clear all results"""
        self.basic_results_text.clear()
        self.timestamp_text.clear()
        self.subtitle_preview.clear()
        self.current_results = None
        self.transcription_result = None
        self.speaker_colors.clear()
        self.speaker_legend_frame.setVisible(False)

        # Reset to initial state
        self.basic_results_text.setPlainText(
            "Ready to transcribe audio files...\n\n"
            "Tips:\n"
            "• Drag and drop audio files into the area above\n"
            "• Use 'Base' model for balanced speed/quality\n"
            "• Enable enhanced preprocessing for noisy audio\n"
            "• Click 'Run Benchmark' to test model performance"
        )

        self.timestamp_text.setPlainText(
            "Timestamped transcript will appear here after transcription...\n\n"
            "Features:\n"
            "• Timestamps show at regular intervals\n"
            "• Text is fully editable for corrections\n"
            "• Export with or without timestamps\n"
            "• Color-coded speaker identification"
        )

    def get_basic_results(self):
        """Get basic results text"""
        return self.basic_results_text.toPlainText()

    def get_timestamped_results(self):
        """Get timestamped results text"""
        return self.timestamp_text.toPlainText()

    def get_current_results(self):
        """Get the current TranscriptionResult object"""
        return self.current_results

    def get_current_text(self):
        """Get currently visible transcription text (for emergency backup)"""
        # Return whichever tab is active
        current_tab = self.results_tabs.currentIndex()
        if current_tab == 0:  # Basic results tab
            text = self.basic_results_text.toPlainText()
        elif current_tab == 1:  # Timestamped tab
            text = self.timestamp_text.toPlainText()
        else:  # Subtitle tab
            text = self.subtitle_preview.toPlainText()

        # Don't return placeholder text
        if (
            text.startswith("Ready to transcribe")
            or text.startswith("Timestamped transcript")
            or text.startswith("Subtitle preview")
        ):
            return ""

        return text
