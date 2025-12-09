import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import QThread, Signal

# Proper API imports - no more path hacking!
from src.core.transcription_service import EnhancedTranscriptionService
from src.models import TranscriptionResult

logger = logging.getLogger(__name__)


@dataclass
class ProcessingSteps:
    FILE_VALIDATION = 0
    AUDIO_QUALITY_ANALYSIS = 1
    AUDIO_PREPROCESSING = 2
    MODEL_LOADING = 3
    TRANSCRIPTION = 4
    POST_PROCESSING = 5

    DESCRIPTIONS = {
        0: "📁 Validating audio file",
        1: "🔍 Analyzing audio quality",
        2: "🎵 Preprocessing audio",
        3: "🧠 Loading AI model",
        4: "🗣️ Transcribing audio",
        5: "⚡ Processing results",
    }


@dataclass
class BatchFile:
    file_path: str
    status: str = "pending"  # pending, processing, completed, failed
    result: Optional[Dict] = None
    error_message: str = ""
    progress: int = 0


class BatchProcessor(QThread):
    # Signals for GUI communication
    file_started = Signal(int, str)  # file_index, filename
    file_progress = Signal(int, int, str, float)  # file_index, step, message, progress
    file_completed = Signal(int, object)  # file_index, result
    file_failed = Signal(int, str)  # file_index, error_message
    batch_completed = Signal()

    def __init__(
        self,
        files: List[BatchFile],
        model: str,
        language: str,
        enhanced: bool,
        speaker_detection: bool,
    ):
        super().__init__()
        self.files = files
        self.model = model
        self.language = language
        self.enhanced = enhanced
        self.speaker_detection = speaker_detection

        # Control flags
        self.should_pause = False
        self.should_stop = False

        self.transcription_service = None

    def run(self):
        try:
            print("\n" + "=" * 60)
            print("🔍 BATCH PROCESSOR DEBUG")
            print("=" * 60)
            print(f"Model received: {self.model}")
            print(f"Language: {self.language}")
            print(f"Enhanced preprocessing: {self.enhanced}")
            print(f"Speaker detection: {self.speaker_detection}")
            print("=" * 60 + "\n")

            # One service shared across batch; keep chosen model fixed
            self.transcription_service = EnhancedTranscriptionService(
                model_size=self.model,
                enable_speaker_detection=self.speaker_detection,
                enable_model_optimization=False,
                enable_audio_enhancement=self.enhanced,
                enable_text_processing=True,
            )

            logger.info(
                f"🔄 Starting batch processing of {len(self.files)} files with {self.model} model"
            )

            for i, batch_file in enumerate(self.files):
                if self.should_stop:
                    logger.info("🛑 Batch processing stopped by user")
                    break

                # Handle pause/resume
                while self.should_pause and not self.should_stop:
                    self.msleep(100)  # Milliseconds

                if self.should_stop:
                    break

                # Start processing this file
                filename = Path(batch_file.file_path).name
                self.file_started.emit(i, filename)
                logger.info(f"📁 Processing file {i + 1}/{len(self.files)}: {filename}")

                try:
                    # Validate file before processing
                    is_valid, validation_msg = self.transcription_service.validate_file(
                        batch_file.file_path
                    )
                    if not is_valid:
                        raise ValueError(f"File validation failed: {validation_msg}")

                    # Process file using professional service
                    result = self._process_single_file(i, batch_file)

                    if result:
                        self.file_completed.emit(i, result.to_dict())
                        logger.info(f"✅ Successfully processed: {filename}")
                    else:
                        raise Exception("Transcription service returned no result")

                except FileNotFoundError as e:
                    error_msg = f"File not found: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    self.file_failed.emit(i, error_msg)
                    # Continue

                except ValueError as e:
                    # Validation errors (corrupt, empty, too long, etc.)
                    error_msg = f"Invalid file: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    self.file_failed.emit(i, error_msg)
                    # Continue

                except PermissionError as e:
                    error_msg = f"Permission denied: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    self.file_failed.emit(i, error_msg)
                    # Continue

                except MemoryError:
                    error_msg = f"Out of memory processing {filename}"
                    logger.error(f"❌ {error_msg}")
                    self.file_failed.emit(i, error_msg)
                    # Try to recover by cleaning up
                    if self.transcription_service:
                        self.transcription_service.cleanup()
                    import gc

                    gc.collect()
                    # Continue

                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"❌ Failed to process {filename}: {error_msg}")
                    self.file_failed.emit(i, error_msg)
                    # Continue

            logger.info("🎉 Batch processing completed")
            self.batch_completed.emit()

        except Exception as e:
            logger.error(f"💥 Batch processing fatal error: {e}")
            self.file_failed.emit(-1, f"Batch processing failed: {e}")
            # End

    def _process_single_file(
        self, file_index: int, batch_file: BatchFile
    ) -> Optional[TranscriptionResult]:
        # Step 1: File validation
        self.file_progress.emit(
            file_index,
            ProcessingSteps.FILE_VALIDATION,
            "Validating audio file...",
            10,
        )

        if not os.path.exists(batch_file.file_path):
            raise Exception(f"Audio file not found: {batch_file.file_path}")

        # Step 2: Quality analysis
        self.file_progress.emit(
            file_index,
            ProcessingSteps.AUDIO_QUALITY_ANALYSIS,
            "Analyzing audio quality...",
            25,
        )

        # Step 3: Preprocessing
        self.file_progress.emit(
            file_index,
            ProcessingSteps.AUDIO_PREPROCESSING,
            "Preprocessing audio...",
            40,
        )

        # Step 4: Model loading (already loaded, but report progress)
        self.file_progress.emit(
            file_index,
            ProcessingSteps.MODEL_LOADING,
            f"Using {self.model.upper()} model...",
            60,
        )

        # Step 5: Transcription
        self.file_progress.emit(
            file_index, ProcessingSteps.TRANSCRIPTION, "🗣️ Transcribing audio...", 70
        )

        # Use professional service for transcription
        transcription_start = time.time()
        language = None if self.language == "auto" else self.language

        result = self.transcription_service.transcribe_file(
            file_path=batch_file.file_path,
            language=language,
            enable_enhancements=self.enhanced,
        )

        transcription_time = time.time() - transcription_start

        # Step 6: Post-processing
        self.file_progress.emit(
            file_index,
            ProcessingSteps.POST_PROCESSING,
            f"⚡ Completed in {transcription_time:.1f}s",
            95,
        )

        # Final progress
        self.file_progress.emit(
            file_index, ProcessingSteps.POST_PROCESSING, "Processing complete", 100
        )

        return result

    def pause(self):
        self.should_pause = True
        logger.info("Batch processing paused")

    def resume(self):
        self.should_pause = False
        logger.info("Batch processing resumed")

    def stop(self):
        self.should_stop = True
        logger.info("Batch processing stop requested")
