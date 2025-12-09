import time

import psutil
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QProgressBar, QStatusBar


class StatusBarComponent(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_time = time.time()
        self.setup_ui()
        self.setup_monitoring()

    def setup_ui(self):
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(300)
        self.progress_bar.setMinimumHeight(25)  # Make it taller and more visible
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3b82f6;
                border-radius: 6px;
                text-align: center;
                background-color: #f1f5f9;
                font-weight: bold;
                font-size: 12px;
                color: #1e293b;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:1 #2563eb);
                border-radius: 4px;
            }
        """)

        self.system_monitor_label = QLabel(
            "Memory: --% | CPU: --% | Uptime: 0s | Status: Ready"
        )
        self.system_monitor_label.setFont(QFont("Monaco", 9))

        self.local_status_label = QLabel("LOCAL PROCESSING")
        self.local_status_label.setFont(QFont("Monaco", 9, QFont.Bold))
        self.local_status_label.setStyleSheet(
            "color: #10b981; "
            "background-color: rgba(16, 185, 129, 0.1); "
            "padding: 2px 6px; "
            "border-radius: 4px;"
        )
        self.local_status_label.setToolTip(
            "All processing happens locally on your device. "
            "No internet required. Zero cloud API calls. Privacy-focused design.\n\n"
            "Click for detailed privacy information"
        )
        self.local_status_label.setCursor(Qt.PointingHandCursor)
        self.local_status_label.mousePressEvent = self._on_privacy_badge_clicked

        self.privacy_audit_label = QLabel("PRIVACY AUDIT: READY")
        self.privacy_audit_label.setFont(QFont("Monaco", 9, QFont.Bold))
        self.privacy_audit_label.setStyleSheet(
            "color: #8b5cf6; "
            "background-color: rgba(139, 92, 246, 0.1); "
            "padding: 2px 6px; "
            "border-radius: 4px;"
        )
        self.privacy_audit_label.setToolTip(
            "Privacy audit monitors for external connections. "
            "All sessions logged. Zero network activity expected. Complete offline verification.\n\n"
            "Click for detailed privacy information"
        )
        self.privacy_audit_label.setCursor(Qt.PointingHandCursor)
        self.privacy_audit_label.mousePressEvent = self._on_privacy_badge_clicked

        self.addWidget(self.system_monitor_label, 1)  # Stretch to take available space
        self.addPermanentWidget(self.privacy_audit_label)
        self.addPermanentWidget(self.local_status_label)
        self.addPermanentWidget(self.progress_bar)

    def setup_monitoring(self):
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.update_system_stats)
        self.monitor_timer.start(2000)  # Update every 2 seconds

        self.update_system_stats()

    def update_system_stats(self):
        try:
            memory_percent = psutil.virtual_memory().percent
            cpu_percent = psutil.cpu_percent(interval=None)
            uptime = int(time.time() - self.start_time)

            if uptime < 60:
                uptime_str = f"{uptime}s"
            elif uptime < 3600:
                minutes = uptime // 60
                seconds = uptime % 60
                uptime_str = f"{minutes}m {seconds}s"
            else:
                hours = uptime // 3600
                minutes = (uptime % 3600) // 60
                uptime_str = f"{hours}h {minutes}m"

            status_text = f"Memory: {memory_percent:.1f}% | CPU: {cpu_percent:.1f}% | Uptime: {uptime_str} | Status: Ready"
            self.system_monitor_label.setText(status_text)

        except Exception:
            self.system_monitor_label.setText(
                "Memory: --% | CPU: --% | Uptime: --s | Status: Ready"
            )

    def show_progress(self, value=0, text="Processing..."):
        self.progress_bar.setValue(value)
        self.progress_bar.setVisible(True)
        self.update_status(f"Status: {text}")

    def update_progress(self, value, text=None):
        self.progress_bar.setValue(value)
        if text:
            self.update_status(f"Status: {text}")

    def hide_progress(self):
        self.progress_bar.setVisible(False)
        self.update_status("Status: Ready")

    def update_status(self, status_text):
        current_text = self.system_monitor_label.text()
        # Replace everything after the last | with new status
        if " | Status: " in current_text:
            base_text = current_text.rsplit(" | Status: ", 1)[0]
            new_text = f"{base_text} | {status_text}"
        else:
            # Fallback if format is unexpected
            new_text = f"{current_text} | {status_text}"

        self.system_monitor_label.setText(new_text)

    def set_privacy_audit_status(self, status, color=None):
        self.privacy_audit_label.setText(f"PRIVACY AUDIT: {status}")

        if color:
            self.privacy_audit_label.setStyleSheet(
                f"color: {color}; "
                "background-color: rgba(139, 92, 246, 0.1); "
                "padding: 2px 6px; "
                "border-radius: 4px;"
            )

    def set_local_processing_status(self, status, color=None):
        self.local_status_label.setText(status)

        if color:
            self.local_status_label.setStyleSheet(
                f"color: {color}; "
                "background-color: rgba(16, 185, 129, 0.1); "
                "padding: 2px 6px; "
                "border-radius: 4px;"
            )

    def show_processing_status(self, operation_name="PROCESSING"):
        self.set_local_processing_status(f"{operation_name} ACTIVE", "#f59e0b")
        self.set_privacy_audit_status("MONITORING", "#8b5cf6")

    def show_ready_status(self):
        self.set_local_processing_status("LOCAL PROCESSING", "#10b981")
        self.set_privacy_audit_status("READY", "#8b5cf6")

    def show_error_status(self):
        self.set_local_processing_status("ERROR", "#dc2626")
        self.set_privacy_audit_status("ALERT", "#dc2626")

    def _on_privacy_badge_clicked(self, event):
        from PySide6.QtWidgets import QMessageBox

        details = """PRIVACY-FIRST DESIGN

100% Offline Processing
  No internet required after initial setup.
  All AI models run locally on your device.

Local AI Models
  OpenAI Whisper models stored on your device.
  No cloud API calls for transcription.

Zero Data Collection
  No telemetry, analytics, or tracking.
  No user data transmitted to any server.

Complete Audit Trail
  Full logging for compliance verification.
  Daily log files stored locally only.

Advanced Security
  - Filename sanitization prevents injection attacks
  - Audio validation prevents malicious files
  - Disk space checks prevent system issues
  - Memory monitoring prevents resource exhaustion
  - Crash recovery with emergency backups

Data Sovereignty
  Your audio and transcriptions stay on your device.
  You have complete control over your data.

Compliance Ready
  - GDPR compliant (no data leaves device)
  - HIPAA compatible (with proper procedures)
  - Zero trust architecture
  - No third-party processors

For detailed compliance documentation, click
the Privacy Report button to generate a
comprehensive privacy compliance report."""

        QMessageBox.information(self.parent(), "Privacy Features", details)

    def cleanup(self):
        if hasattr(self, "monitor_timer"):
            self.monitor_timer.stop()
