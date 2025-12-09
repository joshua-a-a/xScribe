import logging
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

import torch
import whisper

from ..models.transcription_result import TranscriptionResult, TranscriptionSegment
from .audio_enhancer import AudioEnhancer
from .audio_processor import AudioProcessor
from .model_optimizer import ModelConfig, ModelOptimizer
from .subtitle_generator import SubtitleGenerator
from .text_processor import TextPostProcessor

logger = logging.getLogger(__name__)


class EnhancedTranscriptionService:
    def __init__(
        self,
        model_size: str = "base",
        device: Optional[str] = None,
        enable_audio_enhancement: bool = True,
        enable_model_optimization: bool = True,
        enable_text_processing: bool = True,
        enable_speaker_detection: bool = False,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ):
        self.model_size = model_size
        self.device = device
        self.enable_audio_enhancement = enable_audio_enhancement
        self.enable_model_optimization = enable_model_optimization
        self.enable_text_processing = enable_text_processing
        self.enable_speaker_detection = enable_speaker_detection
        self.progress_callback = progress_callback

        self._transcriber = None
        self._loaded_model_size = None
        self._audio_processor = AudioProcessor()

        if enable_audio_enhancement:
            self.audio_enhancer = AudioEnhancer()
        if enable_model_optimization:
            self.model_optimizer = ModelOptimizer()
        if enable_text_processing:
            self.text_processor = TextPostProcessor()

        self.subtitle_generator = SubtitleGenerator()

        self.cache_dir = Path.home() / ".cache" / "whisper"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ["XDG_CACHE_HOME"] = str(Path.home() / ".cache")

        logger.info("Enhanced TranscriptionService initialized")
        logger.info(f"Audio enhancement: {enable_audio_enhancement}")
        logger.info(f"Model optimization: {enable_model_optimization}")
        logger.info(f"Text processing: {enable_text_processing}")

    @property
    def transcriber(self):
        if self._transcriber is None or self._loaded_model_size != self.model_size:
            if self.progress_callback:
                self.progress_callback("Loading AI model...", 10.0)

            # DEBUG: Log actual model being loaded
            if (
                self._loaded_model_size != self.model_size
                and self._loaded_model_size is not None
            ):
                print(
                    f"� MODEL CHANGE: Switching from '{self._loaded_model_size}' to '{self.model_size}'"
                )
            else:
                print(
                    f"�🔍 TRANSCRIPTION SERVICE: Loading Whisper model '{self.model_size}'"
                )

            device = self.device or ("cuda" if torch.cuda.is_available() else "cpu")
            self._transcriber = whisper.load_model(
                self.model_size, device=device, download_root=str(self.cache_dir)
            )
            self._loaded_model_size = self.model_size

            print(
                f"✓ TRANSCRIPTION SERVICE: Model '{self.model_size}' loaded successfully"
            )

            if self.progress_callback:
                self.progress_callback("AI model loaded", 20.0)

        return self._transcriber

    def transcribe_file(
        self,
        file_path: Union[str, Path],
        language: Optional[str] = None,
        domain: Optional[str] = None,
        accuracy_priority: str = "balanced",
        enable_enhancements: bool = True,
    ) -> TranscriptionResult:
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        logger.info(f"🚀 Starting enhanced transcription of: {file_path.name}")
        start_time = time.time()

        try:
            if self.progress_callback:
                self.progress_callback("Analyzing audio quality...", 25.0)

            audio_characteristics = {}
            enhanced_audio = None

            if enable_enhancements and self.enable_audio_enhancement:
                audio_characteristics = self.audio_enhancer.analyze_audio_quality(
                    str(file_path)
                )
                quality_score = audio_characteristics.get("quality_score", 75)

                logger.info(f"📊 Audio quality score: {quality_score:.1f}/100")

                if quality_score < 80 or accuracy_priority == "accuracy":
                    logger.info("🎵 Applying audio enhancements")
                    if self.progress_callback:
                        self.progress_callback("Enhancing audio quality...", 40.0)

                    enhanced_audio, _ = self.audio_enhancer.enhance_audio(
                        str(file_path),
                        enable_noise_reduction=True,
                        enable_speech_enhancement=True,
                        enable_normalization=True,
                        noise_reduction_strength=0.6 if quality_score < 60 else 0.4,
                    )

            optimal_config = None
            if enable_enhancements and self.enable_model_optimization:
                if self.progress_callback:
                    self.progress_callback("Optimizing model configuration...", 50.0)

                optimal_config = self.model_optimizer.optimize_config_for_audio(
                    audio_characteristics, accuracy_priority
                )

                if optimal_config.model_size != self.model_size:
                    logger.info(
                        f"🧠 Switching to optimal model: {optimal_config.model_size}"
                    )
                    self._transcriber = None
                    self.model_size = optimal_config.model_size

                if domain:
                    optimal_config.initial_prompt = (
                        self.model_optimizer.create_domain_specific_prompt(domain)
                    )

            if self.progress_callback:
                self.progress_callback("Transcribing audio...", 60.0)

            transcription_start = time.time()

            if enhanced_audio is not None:
                import tempfile

                import soundfile as sf

                with tempfile.NamedTemporaryFile(
                    suffix=".wav", delete=False
                ) as tmp_file:
                    sf.write(tmp_file.name, enhanced_audio, 16000)
                    temp_audio_path = tmp_file.name

                try:
                    result = self._transcribe_with_config(
                        temp_audio_path, language, optimal_config
                    )
                finally:
                    os.unlink(temp_audio_path)
            else:
                result = self._transcribe_with_config(
                    str(file_path), language, optimal_config
                )

            transcription_time = time.time() - transcription_start

            if enable_enhancements and self.enable_text_processing and result:
                if self.progress_callback:
                    self.progress_callback("Post-processing text...", 85.0)

                logger.info("📝 Applying text post-processing")

                if "segments" in result and result["segments"]:
                    processed_segments = self.text_processor.batch_process(
                        result["segments"], domain
                    )
                    result["segments"] = processed_segments

                if "text" in result:
                    result["text"] = self.text_processor.process_text(
                        result["text"], domain
                    )

            processing_time = time.time() - start_time

            if self.progress_callback:
                self.progress_callback("Finalizing results...", 95.0)

            transcription_result = self._create_enhanced_result(
                result,
                processing_time,
                transcription_time,
                audio_characteristics,
                file_path,
            )

            if (
                enable_enhancements
                and self.enable_model_optimization
                and optimal_config
            ):
                quality_metrics = {
                    "text_length": len(transcription_result.full_text),
                    "segment_count": len(transcription_result.segments),
                    "avg_confidence": transcription_result.average_confidence or 0.0,
                }

                audio_duration = audio_characteristics.get(
                    "duration",
                    len(enhanced_audio) / 16000 if enhanced_audio is not None else 60,
                )

                self.model_optimizer.monitor_performance(
                    optimal_config, processing_time, audio_duration, quality_metrics
                )

            if self.progress_callback:
                self.progress_callback("Transcription completed!", 100.0)

            logger.info(
                f"✅ Enhanced transcription completed in {processing_time:.2f}s"
            )
            logger.info(
                f"📊 Result: {len(transcription_result.full_text)} chars, "
                f"{len(transcription_result.segments)} segments"
            )

            return transcription_result

        except Exception as e:
            error_msg = f"Enhanced transcription failed: {str(e)}"
            logger.error(error_msg)
            if self.progress_callback:
                self.progress_callback(f"Error: {e}", 0.0)
            raise RuntimeError(error_msg)

    def _transcribe_with_config(
        self, audio_path: str, language: Optional[str], config: Optional[ModelConfig]
    ) -> Dict[str, Any]:
        transcriber = self.transcriber

        device = getattr(transcriber, "device", None)
        if device is not None:
            device_type = getattr(device, "type", str(device))
        else:
            device_type = getattr(self, "device", None) or (
                "cuda" if torch.cuda.is_available() else "cpu"
            )

        options: Dict[str, Any] = {
            "language": language,
            "task": "transcribe",
            "verbose": False,
            "word_timestamps": True,
        }

        if device_type == "cpu":
            options["fp16"] = False

        result = transcriber.transcribe(audio_path, **options)

        if "segments" in result:
            base_confidence = result.get("language_probability", 0.9)
            for segment in result["segments"]:
                if "confidence" not in segment:
                    segment["confidence"] = min(base_confidence, 0.95)

        return result

    def _create_enhanced_result(
        self,
        raw_result: Dict[str, Any],
        processing_time: float,
        transcription_time: float,
        audio_characteristics: Dict[str, Any],
        file_path: Path,
    ) -> TranscriptionResult:
        if raw_result is None:
            raw_result = {
                "text": "",
                "segments": [],
                "language": "unknown",
                "language_probability": 0.0,
                "duration": 0.0,
            }

        if self.enable_speaker_detection and raw_result.get("segments"):
            try:
                logger.info("🎭 Applying speaker diarization...")
                from .speaker_diarization import add_speaker_labels

                raw_result["segments"] = add_speaker_labels(
                    str(file_path), raw_result["segments"]
                )
                logger.info("✅ Speaker diarization completed")
            except Exception as e:
                logger.warning(f"Speaker diarization failed: {e}")
                logger.warning("Continuing without speaker labels")

        segments = []
        if raw_result.get("segments"):
            logger.info(
                f"📝 Processing {len(raw_result['segments'])} segments with timestamps"
            )
            for raw_segment in raw_result["segments"]:
                segment = TranscriptionSegment(
                    start=float(raw_segment.get("start", 0.0)),
                    end=float(raw_segment.get("end", 0.0)),
                    text=raw_segment.get("text", ""),
                    confidence=float(raw_segment.get("confidence", 0.0)),
                    speaker=raw_segment.get("speaker"),
                )
                segments.append(segment)
            if segments:
                logger.info(
                    f"   First segment: {segments[0].start:.2f}s - {segments[0].end:.2f}s"
                )
                if segments[0].speaker:
                    logger.info(f"   Speaker: {segments[0].speaker}")

        if not segments:
            text = raw_result.get("text", "").strip()
            if not text:
                text = "[No transcription available]"

            duration = max(float(raw_result.get("duration", 0.0)), 0.1)
            segments = [
                TranscriptionSegment(start=0.0, end=duration, text=text, confidence=0.0)
            ]

        enhanced_metadata = {
            "transcription_time": transcription_time,
            "audio_quality": audio_characteristics,
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size if file_path.exists() else 0,
            "timestamp": time.time(),
        }

        duration = max(float(raw_result.get("duration", 0.0)), 0.1)
        if segments:
            max_segment_end = max(seg.end for seg in segments if seg.end > 0)
            if max_segment_end > duration:
                duration = max_segment_end

        transcription_result = TranscriptionResult(
            segments=segments,
            language=raw_result.get("language", "unknown"),
            language_probability=float(raw_result.get("language_probability", 0.0)),
            duration=duration,
            processing_time=processing_time,
            model_used=self.model_size,
            word_timestamps=raw_result.get("word_timestamps"),
            file_path=file_path,
            metadata=enhanced_metadata,
        )

        return transcription_result

    def get_available_models(self) -> Dict[str, str]:
        return {
            "tiny": "Fastest, least accurate",
            "base": "Good balance of speed and accuracy",
            "small": "Better accuracy, slower",
            "medium": "High accuracy, moderate speed",
            "large": "Best accuracy, slowest",
        }

    def get_supported_formats(self) -> list[str]:
        return [".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg"]

    def validate_file(self, file_path: Union[str, Path]) -> tuple[bool, str]:
        return self._audio_processor.validate_audio_file(file_path)

    def generate_subtitles(
        self, transcription_result: TranscriptionResult, format: str = "srt"
    ) -> str:
        return self.subtitle_generator.generate_subtitles(
            transcription_result, format, transcription_result.word_timestamps
        )

    def transcribe_and_generate_subtitles(
        self,
        file_path: Union[str, Path],
        subtitle_format: str = "srt",
        language: Optional[str] = None,
        save_subtitle_file: bool = False,
    ) -> tuple[TranscriptionResult, str]:
        logger.info(
            f"🎬 Starting transcription and subtitle generation for: {file_path}"
        )

        transcription_result = self.transcribe_file(file_path, language)

        subtitles = self.generate_subtitles(transcription_result, subtitle_format)

        if save_subtitle_file:
            audio_path = Path(file_path)
            subtitle_path = audio_path.with_suffix(f".{subtitle_format}")

            with open(subtitle_path, "w", encoding="utf-8") as f:
                f.write(subtitles)

            logger.info(f"📁 Subtitles saved to: {subtitle_path}")

        return transcription_result, subtitles

    def cleanup(self):
        if self._transcriber is not None:
            import gc

            logger.info(
                f"🧹 Cleaning up Whisper model '{self._loaded_model_size}' from memory"
            )

            del self._transcriber
            self._transcriber = None
            self._loaded_model_size = None

            gc.collect()

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info("✓ Model cleanup complete")


class TranscriptionService(EnhancedTranscriptionService):
    def __init__(
        self,
        model_size: str = "base",
        device: Optional[str] = None,
        enable_speaker_detection: bool = False,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ):
        super().__init__(
            model_size=model_size,
            device=device,
            enable_audio_enhancement=True,
            enable_model_optimization=True,
            enable_text_processing=True,
            progress_callback=progress_callback,
        )
        self.enable_speaker_detection = enable_speaker_detection

    def transcribe_file(
        self,
        file_path: Union[str, Path],
        language: Optional[str] = None,
        enhanced_processing: bool = True,
    ) -> TranscriptionResult:
        return super().transcribe_file(
            file_path=file_path,
            language=language,
            domain=None,
            accuracy_priority="balanced",
            enable_enhancements=enhanced_processing,
        )
