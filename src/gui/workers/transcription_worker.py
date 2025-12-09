import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import QThread, Signal

# Professional API imports -- no more path hacking!
from src.core.transcription_service import (
    EnhancedTranscriptionService,  # Use the enhanced service with word timestamps
)

# Set up logging
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
        0: "Validating audio file",
        1: "Analyzing audio quality",
        2: "Preprocessing audio",
        3: "Loading AI model",
        4: "Transcribing audio",
        5: "Processing results",
    }


class TranscriptionWorker(QThread):
    # Signals for GUI communication
    progress_updated = Signal(int, str, float)  # step, message, progress
    step_completed = Signal(str)  # message
    transcription_finished = Signal(object)  # result (TranscriptionResult.to_dict())
    error_occurred = Signal(str)  # error message

    def __init__(
        self,
        file_path: str,
        model: str,
        language: str,
        enhanced: bool,
        speaker_detection: bool,
        word_timestamps: bool = True,
    ):
        super().__init__()
        self.file_path = file_path
        self.model = model
        self.language = language
        self.enhanced = enhanced
        self.speaker_detection = speaker_detection
        self.word_timestamps = word_timestamps

        # Initialized lazily in run() so we honor the user's latest settings
        self.transcription_service = None

    def run(self):
        try:
            logger.info(
                f"🎵 Starting transcription: {os.path.basename(self.file_path)}"
            )

            # Generate session ID for privacy auditing (professional logging)
            session_id = (
                f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(self)}"
            )

            # Step 1: File validation
            self.progress_updated.emit(
                ProcessingSteps.FILE_VALIDATION, "📁 Validating audio file...", 10
            )

            if not os.path.exists(self.file_path):
                raise Exception(f"Audio file not found: {self.file_path}")

            # Step 2: Audio quality analysis
            self.progress_updated.emit(
                ProcessingSteps.AUDIO_QUALITY_ANALYSIS,
                "Analyzing audio quality...",
                25,
            )

            # Step 3: Preprocessing
            self.progress_updated.emit(
                ProcessingSteps.AUDIO_PREPROCESSING, "🎵 Preprocessing audio...", 40
            )

            # Step 4: Model loading - Create transcription service with proper config
            self.progress_updated.emit(
                ProcessingSteps.MODEL_LOADING,
                f"Loading {self.model.upper()} model...",
                60,
            )

            def progress_callback(message, progress):
                # Convert service progress (0-100) to our step progress (60-70)
                adjusted_progress = 60 + (progress / 100.0) * 10
                self.progress_updated.emit(
                    ProcessingSteps.MODEL_LOADING, message, adjusted_progress
                )

            self.transcription_service = EnhancedTranscriptionService(
                model_size=self.model,
                enable_speaker_detection=self.speaker_detection,
                enable_model_optimization=False,
                enable_audio_enhancement=self.enhanced,
                enable_text_processing=True,
                progress_callback=progress_callback,
            )

            self.progress_updated.emit(
                ProcessingSteps.MODEL_LOADING, "🧠 Model loaded", 65
            )

            # Step 5: Transcription with real-time progress
            transcription_start_time = time.time()
            self.progress_updated.emit(
                ProcessingSteps.TRANSCRIPTION, "🗣️ Transcribing audio...", 70
            )

            language = None if self.language == "auto" else self.language

            result = self.transcription_service.transcribe_file(
                file_path=self.file_path,
                language=language,
                enable_enhancements=self.enhanced,
            )

            if not result:
                raise Exception("Transcription service returned no result")

            # Update progress with actual performance
            actual_time = time.time() - transcription_start_time

            # Performance feedback
            self.progress_updated.emit(
                ProcessingSteps.TRANSCRIPTION,
                f"Transcribed in {actual_time:.1f}s",
                85,
            )

            # Step 6: Post-processing
            self.progress_updated.emit(
                ProcessingSteps.POST_PROCESSING, "⚡ Finalizing results...", 95
            )

            # Final step completion
            self.step_completed.emit("🎉 Transcription completed successfully!")

            # Convert to dict for GUI compatibility
            result_dict = result.to_dict()

            logger.info(
                f"Transcription completed: {os.path.basename(self.file_path)} "
                f"({actual_time:.1f}s, {len(result_dict.get('segments', []))} segments)"
            )

            # Send result to GUI
            self.transcription_finished.emit(result_dict)

        except Exception as e:
            error_msg = str(e)
            logger.error(
                f"Transcription failed for {os.path.basename(self.file_path)}: {error_msg}"
            )
            self.error_occurred.emit(error_msg)
