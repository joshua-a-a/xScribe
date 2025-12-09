import logging
import warnings
from typing import Any, Dict, Tuple

import librosa
import noisereduce as nr
import numpy as np
import scipy.ndimage
import scipy.signal

# Suppress librosa warnings
warnings.filterwarnings("ignore", category=UserWarning, module="librosa")

logger = logging.getLogger(__name__)


class AudioEnhancer:
    def __init__(self, target_sr: int = 16000):
        self.target_sr = target_sr
        self.logger = logging.getLogger(__name__)

    def analyze_audio_quality(self, audio_path: str) -> Dict[str, Any]:
        try:
            y, sr = librosa.load(audio_path, sr=None)

            if len(y) == 0:
                return {
                    "quality_score": 0.0,
                    "duration": 0.0,
                    "error": "Empty audio file",
                    "recommendations": ["Audio file appears to be empty or invalid"],
                }

            duration = len(y) / sr

            try:
                rms = librosa.feature.rms(y=y)[0]
                spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            except Exception as e:
                self.logger.warning(f"Spectral analysis failed: {e}")
                rms = np.array([np.sqrt(np.mean(y**2))])
                spectral_centroid = np.array([sr / 4])  # Default estimate

            frame_length = int(0.025 * sr)  # 25ms frames
            hop_length = int(0.010 * sr)  # 10ms hop

            signal_threshold = np.percentile(np.abs(y), 90)
            noise_threshold = np.percentile(np.abs(y), 10)

            if noise_threshold > 0 and signal_threshold > noise_threshold:
                snr_estimate = 20 * np.log10(signal_threshold / noise_threshold)
            else:
                snr_estimate = 0.0  # Poor SNR

            clipped_samples = np.sum(np.abs(y) > 0.99)
            clipping_ratio = clipped_samples / len(y) if len(y) > 0 else 0.0

            silent_samples = np.sum(np.abs(y) < 0.01)
            silence_ratio = silent_samples / len(y) if len(y) > 0 else 1.0

            quality_score = 50.0  # Base score

            if not np.isnan(snr_estimate) and not np.isinf(snr_estimate):
                if snr_estimate > 20:
                    quality_score += 20
                elif snr_estimate > 10:
                    quality_score += 10
                elif snr_estimate < 5:
                    quality_score -= 20

            if clipping_ratio < 0.01:
                quality_score += 10
            elif clipping_ratio > 0.05:
                quality_score -= 20

            if 0.1 < silence_ratio < 0.3:
                quality_score += 10
            elif silence_ratio > 0.5:
                quality_score -= 15

            mean_spectral_centroid = np.mean(spectral_centroid)
            if (
                not np.isnan(mean_spectral_centroid)
                and 1000 < mean_spectral_centroid < 4000
            ):
                quality_score += 10

            quality_score = max(0, min(100, quality_score))

            recommendations = []
            if np.isnan(snr_estimate) or snr_estimate < 15:
                recommendations.append("Enable noise reduction")
            if clipping_ratio > 0.02:
                recommendations.append("Audio may be clipped - check levels")
            if silence_ratio > 0.4:
                recommendations.append("Consider trimming silence")
            if not np.isnan(mean_spectral_centroid) and mean_spectral_centroid < 800:
                recommendations.append(
                    "Audio may benefit from high-frequency enhancement"
                )

            return {
                "quality_score": float(quality_score),
                "duration": float(duration),
                "sample_rate": int(sr),
                "snr_estimate": float(snr_estimate)
                if not np.isnan(snr_estimate)
                else 0.0,
                "clipping_ratio": float(clipping_ratio),
                "silence_ratio": float(silence_ratio),
                "mean_spectral_centroid": float(mean_spectral_centroid)
                if not np.isnan(mean_spectral_centroid)
                else 0.0,
                "recommendations": recommendations,
            }

        except Exception as e:
            self.logger.error(f"Audio quality analysis failed: {e}")
            return {
                "quality_score": 50.0,
                "duration": 0.0,
                "error": str(e),
                "recommendations": ["Audio analysis failed - using default settings"],
            }

    def enhance_audio(
        self,
        audio_path: str,
        enable_noise_reduction: bool = True,
        enable_speech_enhancement: bool = True,
        enable_normalization: bool = True,
        noise_reduction_strength: float = 0.5,
        target_lufs: float = -23.0,
    ) -> Tuple[np.ndarray, int]:
        try:
            logger.info(f"🎵 Loading audio: {audio_path}")

            y, sr = librosa.load(audio_path, sr=self.target_sr)
            original_length = len(y)

            logger.info(f"📊 Original: {sr}Hz, {len(y)} samples ({len(y) / sr:.2f}s)")

            y = y - np.mean(y)

            y_trimmed, trim_indices = librosa.effects.trim(y, top_db=30)
            logger.info(f"✂️ Trimmed {original_length - len(y_trimmed)} silent samples")

            if enable_noise_reduction and len(y_trimmed) > 0:
                logger.info(
                    f"🔇 Applying noise reduction (strength: {noise_reduction_strength})"
                )

                try:
                    # Use noisereduce library for spectral noise reduction
                    y_denoised = nr.reduce_noise(
                        y=y_trimmed,
                        sr=self.target_sr,
                        prop_decrease=noise_reduction_strength,
                        stationary=False,  # Non-stationary noise reduction
                    )
                    y_trimmed = y_denoised
                except Exception as e:
                    logger.warning(f"Noise reduction failed: {e}, continuing without")

            if enable_speech_enhancement:
                logger.info("🗣️ Applying speech enhancement")
                y_trimmed = self._apply_speech_filter(y_trimmed, self.target_sr)

            y_trimmed = self._apply_compression(y_trimmed)

            if enable_normalization:
                logger.info(f"📈 Normalizing to {target_lufs} LUFS")
                y_trimmed = self._normalize_audio(y_trimmed, target_lufs)

            final_rms = np.sqrt(np.mean(y_trimmed**2))
            logger.info(
                f"✅ Enhanced audio: RMS={final_rms:.4f}, Length={len(y_trimmed)} samples"
            )

            return y_trimmed, self.target_sr

        except Exception as e:
            logger.error(f"Audio enhancement failed: {e}")
            # Return original audio as fallback
            y_fallback, sr_fallback = librosa.load(audio_path, sr=self.target_sr)
            return y_fallback, sr_fallback

    def _apply_speech_filter(self, y: np.ndarray, sr: int) -> np.ndarray:
        try:
            nyquist = sr // 2
            low_freq = 80 / nyquist
            high_freq = 8000 / nyquist
            low_freq = max(0.001, min(low_freq, 0.99))
            high_freq = max(low_freq + 0.001, min(high_freq, 0.99))

            b, a = scipy.signal.butter(4, [low_freq, high_freq], btype="band")
            y_filtered = scipy.signal.filtfilt(b, a, y)

            pre_emphasis = 0.95
            y_filtered = np.append(
                y_filtered[0], y_filtered[1:] - pre_emphasis * y_filtered[:-1]
            )

            return y_filtered

        except Exception as e:
            logger.warning(f"Speech filtering failed: {e}")
            return y

    def _apply_compression(
        self, y: np.ndarray, ratio: float = 3.0, threshold: float = -12.0
    ) -> np.ndarray:
        try:
            threshold_linear = 10 ** (threshold / 20.0)

            envelope = np.abs(y)

            compressed = np.where(
                envelope > threshold_linear,
                threshold_linear + (envelope - threshold_linear) / ratio,
                envelope,
            )

            y_compressed = y * (compressed / (envelope + 1e-8))

            return y_compressed

        except Exception as e:
            logger.warning(f"Compression failed: {e}")
            return y

    def _normalize_audio(self, y: np.ndarray, target_lufs: float = -23.0) -> np.ndarray:
        try:
            current_rms = np.sqrt(np.mean(y**2))

            if current_rms > 0:
                target_rms = 10 ** (target_lufs / 20.0)

                gain = target_rms / current_rms

                y_normalized = y * gain

                y_normalized = np.tanh(y_normalized * 0.95)

                return y_normalized
            else:
                return y

        except Exception as e:
            logger.warning(f"Normalization failed: {e}")
            return y

    def batch_enhance_directory(
        self, input_dir: str, output_dir: str, **enhancement_params
    ) -> Dict[str, Any]:
        from pathlib import Path

        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        audio_extensions = {".wav", ".mp3", ".flac", ".m4a", ".ogg", ".aac"}
        audio_files = [
            f for f in input_path.glob("*") if f.suffix.lower() in audio_extensions
        ]

        results = {
            "processed": 0,
            "failed": 0,
            "total": len(audio_files),
            "failed_files": [],
        }

        for audio_file in audio_files:
            try:
                logger.info(f"Processing: {audio_file.name}")

                enhanced_audio, sr = self.enhance_audio(
                    str(audio_file), **enhancement_params
                )

                output_file = output_path / f"enhanced_{audio_file.stem}.wav"
                import soundfile as sf

                sf.write(str(output_file), enhanced_audio, sr)

                results["processed"] += 1

            except Exception as e:
                logger.error(f"Failed to process {audio_file.name}: {e}")
                results["failed"] += 1
                results["failed_files"].append(str(audio_file))

        return results
