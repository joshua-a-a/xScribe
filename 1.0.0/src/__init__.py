__version__ = "1.0.0"
__author__ = "Josh Poulter"
__email__ = "josh@macmasters.tech"

from .core.audio_processor import AudioProcessor
from .core.transcription_service import (
    EnhancedTranscriptionService,
    TranscriptionService,
)
from .models.transcription_result import TranscriptionResult, TranscriptionSegment

__all__ = [
    "TranscriptionService",
    "EnhancedTranscriptionService",
    "AudioProcessor",
    "TranscriptionResult",
    "TranscriptionSegment",
]
