import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import librosa
import numpy as np

logger = logging.getLogger(__name__)


class SpeakerDiarization:
    def __init__(
        self,
        n_speakers: Optional[int] = None,
        min_speakers: int = 1,
        max_speakers: int = 10,
    ):
        self.n_speakers = n_speakers
        self.min_speakers = min_speakers
        self.max_speakers = max_speakers

    def detect_speakers(
        self, audio_path: str, segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        try:
            logger.info(f"🎭 Starting speaker diarization for {Path(audio_path).name}")

            y, sr = librosa.load(audio_path, sr=16000)

            segment_features = []
            for seg in segments:
                start_sample = int(seg.get("start", 0) * sr)
                end_sample = int(seg.get("end", len(y) / sr) * sr)

                segment_audio = y[start_sample:end_sample]

                if len(segment_audio) > 0:
                    features = self._extract_speaker_features(segment_audio, sr)
                    segment_features.append(features)
                else:
                    segment_features.append(None)

            speaker_labels = self._cluster_speakers(segment_features)

            labeled_segments = []
            for i, seg in enumerate(segments):
                seg_copy = seg.copy()
                if i < len(speaker_labels) and speaker_labels[i] is not None:
                    seg_copy["speaker"] = f"SPEAKER_{speaker_labels[i] + 1}"
                else:
                    seg_copy["speaker"] = None
                labeled_segments.append(seg_copy)

            unique_speakers = len(
                set(label for label in speaker_labels if label is not None)
            )
            logger.info(f"✅ Detected {unique_speakers} unique speakers")

            return labeled_segments

        except Exception as e:
            logger.warning(f"Speaker diarization failed: {e}")
            logger.warning("Continuing without speaker labels")
            return [{"speaker": None, **seg} for seg in segments]

    def _extract_speaker_features(self, audio: np.ndarray, sr: int) -> np.ndarray:
        try:
            if len(audio) < sr // 10:
                return np.zeros(20)

            mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
            mfcc_mean = np.mean(mfccs, axis=1)

            spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)
            centroid_mean = np.mean(spectral_centroid)

            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)
            rolloff_mean = np.mean(spectral_rolloff)

            zcr = librosa.feature.zero_crossing_rate(audio)
            zcr_mean = np.mean(zcr)

            rms = librosa.feature.rms(y=audio)
            rms_mean = np.mean(rms)

            features = np.concatenate(
                [mfcc_mean, [centroid_mean, rolloff_mean, zcr_mean, rms_mean]]
            )

            return features

        except Exception as e:
            logger.warning(f"Feature extraction failed: {e}")
            return np.zeros(20)

    def _cluster_speakers(
        self, features: List[Optional[np.ndarray]]
    ) -> List[Optional[int]]:
        try:
            valid_features = []
            valid_indices = []
            for i, feat in enumerate(features):
                if feat is not None and not np.all(feat == 0):
                    valid_features.append(feat)
                    valid_indices.append(i)

            if not valid_features:
                return [None] * len(features)

            X = np.array(valid_features)

            from sklearn.preprocessing import StandardScaler

            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            n_clusters = self.n_speakers
            if n_clusters is None:
                n_clusters = min(
                    max(
                        self.min_speakers, len(X) // 20
                    ),  # At least 1 speaker per 20 segments
                    self.max_speakers,
                )
                n_clusters = max(n_clusters, 1)

            from sklearn.cluster import AgglomerativeClustering

            clustering = AgglomerativeClustering(n_clusters=n_clusters, linkage="ward")

            labels = clustering.fit_predict(X_scaled)

            result = [None] * len(features)
            for i, idx in enumerate(valid_indices):
                result[idx] = int(labels[i])

            return result

        except Exception as e:
            logger.warning(f"Speaker clustering failed: {e}")
            # Fall back to single speaker
            return [0 if feat is not None else None for feat in features]


def add_speaker_labels(
    audio_path: str, segments: List[Dict[str, Any]], n_speakers: Optional[int] = None
) -> List[Dict[str, Any]]:
    diarizer = SpeakerDiarization(n_speakers=n_speakers)
    return diarizer.detect_speakers(audio_path, segments)
