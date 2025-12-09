import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class AppInstanceManager:
    _instance: Optional["AppInstanceManager"] = None
    _main_window = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def set_main_window(self, window):
        self._main_window = window
        logger.info("Main window registered with AppInstanceManager")

    def get_main_window(self):
        return self._main_window

    def clear(self):
        self._main_window = None

    def emergency_save_state(self):
        if not self._main_window:
            logger.warning("No main window instance available for emergency save")
            return False

        try:
            saved_something = False
            emergency_dir = Path.home() / "Desktop" / "xScribe_Emergency_Backup"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if self._save_batch_results(emergency_dir, timestamp):
                saved_something = True

            if self._save_current_transcription(emergency_dir, timestamp):
                saved_something = True

            self._cleanup_workers()

            if saved_something:
                logger.info("✅ Emergency save completed successfully")
            else:
                logger.info("Emergency save: No active work to save")

            return True

        except Exception as e:
            logger.error(f"Error during emergency save: {e}", exc_info=True)
            return False

    def _save_batch_results(self, emergency_dir: Path, timestamp: str) -> bool:
        try:
            if not hasattr(self._main_window, "batch_results"):
                return False

            if not self._main_window.batch_results:
                return False

            logger.info(
                f"Emergency save: {len(self._main_window.batch_results)} batch results"
            )

            emergency_dir.mkdir(parents=True, exist_ok=True)
            backup_file = emergency_dir / f"emergency_batch_{timestamp}.json"

            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(
                    self._main_window.batch_results, f, indent=2, ensure_ascii=False
                )

            logger.info(f"✅ Emergency batch backup saved to: {backup_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save batch results: {e}")
            return False

    def _save_current_transcription(self, emergency_dir: Path, timestamp: str) -> bool:
        try:
            if not hasattr(self._main_window, "results"):
                return False

            try:
                from PySide6.QtCore import QObject

                if not isinstance(self._main_window.results, QObject):
                    return False

                current_text = self._main_window.results.get_current_text()
            except RuntimeError:
                # Qt object already deleted
                logger.info(
                    "Results widget already deleted, skipping transcription save"
                )
                return False

            if not current_text or len(current_text) == 0:
                return False

            logger.info("Emergency save: Current transcription visible")

            emergency_dir.mkdir(parents=True, exist_ok=True)
            backup_file = emergency_dir / f"emergency_transcription_{timestamp}.txt"

            with open(backup_file, "w", encoding="utf-8") as f:
                f.write(current_text)

            logger.info(f"✅ Emergency transcription saved to: {backup_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save current transcription: {e}")
            return False

    def _cleanup_workers(self):
        try:
            if (
                hasattr(self._main_window, "current_worker")
                and self._main_window.current_worker
            ):
                if self._main_window.current_worker.isRunning():
                    logger.info("Stopping active transcription worker...")
                    self._main_window.current_worker.terminate()
                    self._main_window.current_worker.wait(1000)

            if (
                hasattr(self._main_window, "batch_processor")
                and self._main_window.batch_processor
            ):
                if self._main_window.batch_processor.isRunning():
                    logger.info("Stopping active batch processor...")
                    self._main_window.batch_processor.terminate()
                    self._main_window.batch_processor.wait(1000)

        except Exception as e:
            logger.error(f"Error cleaning up workers: {e}")
