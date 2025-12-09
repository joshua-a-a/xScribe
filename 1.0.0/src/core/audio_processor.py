import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class AudioProcessor:
    def __init__(self):
        self.supported_formats = {
            ".wav",
            ".mp3",
            ".flac",
            ".m4a",
            ".ogg",
            ".opus",
            ".webm",
        }

        self.supported_video_formats = {
            ".mp4",
            ".m4v",
            ".mov",
            ".avi",
            ".mkv",
            ".webm",
            ".flv",
            ".wmv",
            ".mpg",
            ".mpeg",
            ".3gp",
            ".ogv",
            ".vob",
            ".mts",
            ".m2ts",
            ".ts",
            ".divx",
            ".xvid",
            ".asf",
            ".rm",
            ".rmvb",
        }

        self._video_processor = None

    @property
    def video_processor(self):
        if self._video_processor is None:
            from src.core.video_processor import VideoProcessor

            self._video_processor = VideoProcessor()
        return self._video_processor

    def is_video_file(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in self.supported_video_formats

    def is_supported_file(self, file_path: str) -> bool:
        suffix = Path(file_path).suffix.lower()
        return (
            suffix in self.supported_formats or suffix in self.supported_video_formats
        )

    def process_audio(
        self, file_path: str, enhanced: bool = True
    ) -> Tuple[str, Optional[str]]:
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if self.is_video_file(file_path):
            logger.info(f"Video file detected: {file_path_obj.name}")
            try:
                audio_path = self.video_processor.extract_audio(file_path)
                logger.info(f"Audio extracted from video: {audio_path}")
                return audio_path, "video"
            except Exception as e:
                raise RuntimeError(f"Failed to extract audio from video: {str(e)}")

        is_valid, message = self.validate_audio_file(file_path)
        if not is_valid:
            raise ValueError(message)

        return str(file_path), None

    def validate_audio_file(self, file_path: str) -> Tuple[bool, str]:
        try:
            file_path_obj = Path(file_path)

            if not file_path_obj.exists():
                return False, f"File not found: {file_path}"

            if not file_path_obj.is_file():
                return False, f"Not a file: {file_path}"

            suffix = file_path_obj.suffix.lower()
            is_audio = suffix in self.supported_formats
            is_video = suffix in self.supported_video_formats

            if not (is_audio or is_video):
                return False, f"Unsupported format: {suffix}"

            file_size = file_path_obj.stat().st_size

            if file_size < 1024:  # Less than 1KB is likely corrupt/empty
                return (
                    False,
                    f"File too small ({file_size} bytes) - possibly empty or corrupt",
                )

            size_mb = file_size / (1024 * 1024)
            if size_mb > 10240:  # 10GB
                return False, f"File too large: {size_mb:.1f}MB (max 10GB)"

            try:
                import whisper

                audio = whisper.load_audio(str(file_path_obj))

                if len(audio) == 0:
                    return False, "Audio file contains no data (corrupt or empty)"

                duration_seconds = len(audio) / 16000

                if duration_seconds < 0.1:
                    return (
                        False,
                        f"Audio too short: {duration_seconds:.2f}s (minimum 0.1s)",
                    )

                max_duration = 14400  # 4 hours in seconds
                if duration_seconds > max_duration:
                    duration_mins = duration_seconds / 60
                    max_mins = max_duration / 60
                    return (
                        False,
                        f"Audio too long: {duration_mins:.1f} minutes (max {max_mins:.0f} minutes)",
                    )

                if duration_seconds > 1800:  # 30 minutes
                    duration_mins = duration_seconds / 60
                    return (
                        True,
                        f"LONG_FILE:{duration_mins:.1f}",
                    )  # Special marker for confirmation dialog

                return True, f"Valid audio file ({duration_seconds:.1f}s)"

            except Exception as audio_error:
                return False, f"Corrupt or invalid audio file: {str(audio_error)}"

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def get_audio_info(self, file_path: str) -> Dict[str, any]:
        try:
            file_path_obj = Path(file_path)

            if not file_path_obj.exists():
                return {
                    "filename": file_path_obj.name,
                    "format": file_path_obj.suffix.lower(),
                    "exists": False,
                    "error": "File not found",
                }

            return {
                "filename": file_path_obj.name,
                "format": file_path_obj.suffix.lower(),
                "size_bytes": file_path_obj.stat().st_size,
                "size_mb": file_path_obj.stat().st_size / (1024 * 1024),
                "exists": True,
                "path": str(file_path_obj.absolute()),
            }

        except Exception as e:
            return {
                "filename": Path(file_path).name,
                "format": Path(file_path).suffix.lower(),
                "exists": False,
                "error": str(e),
            }
