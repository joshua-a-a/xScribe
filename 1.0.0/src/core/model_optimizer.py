import logging
import time
from dataclasses import dataclass
from typing import Any, Dict

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    model_size: str = "base"
    temperature: float = 0.0
    beam_size: int = 5
    best_of: int = 5
    patience: float = 1.0
    length_penalty: float = 1.0
    compression_ratio_threshold: float = 2.4
    logprob_threshold: float = -1.0
    no_speech_threshold: float = 0.6
    condition_on_previous_text: bool = True
    initial_prompt: str = ""
    suppress_tokens: str = ""
    fp16: bool = False

    @classmethod
    def for_high_accuracy(cls) -> "ModelConfig":
        return cls(
            temperature=0.0,
            beam_size=10,
            best_of=10,
            patience=2.0,
            length_penalty=1.0,
            compression_ratio_threshold=2.0,
            logprob_threshold=-0.5,
            no_speech_threshold=0.7,
            condition_on_previous_text=True,
        )

    @classmethod
    def for_speed(cls) -> "ModelConfig":
        return cls(
            temperature=0.0,
            beam_size=1,
            best_of=1,
            patience=0.5,
            compression_ratio_threshold=3.0,
            logprob_threshold=-1.5,
            no_speech_threshold=0.5,
        )

    @classmethod
    def for_noisy_audio(cls) -> "ModelConfig":
        return cls(
            temperature=0.1,
            beam_size=8,
            best_of=8,
            patience=2.0,
            length_penalty=0.8,
            compression_ratio_threshold=1.8,
            logprob_threshold=-0.3,
            no_speech_threshold=0.8,
            condition_on_previous_text=False,
        )


class ModelOptimizer:
    def __init__(self):
        self.performance_history = []
        self.optimal_configs = {}

    def select_optimal_model_size(
        self,
        audio_duration_minutes: float,
        audio_quality_score: float,
        accuracy_priority: str = "balanced",
    ) -> str:
        if accuracy_priority == "speed":
            if audio_duration_minutes <= 5:
                return "tiny"
            elif audio_duration_minutes <= 15:
                return "base"
            else:
                return "small"

        elif accuracy_priority == "accuracy":
            if audio_quality_score >= 80:
                if audio_duration_minutes <= 30:
                    return "large"
                else:
                    return "medium"
            else:
                return "large"

        else:  # balanced
            if audio_quality_score >= 90:
                return "base"
            elif audio_quality_score >= 70:
                return "small"
            elif audio_quality_score >= 50:
                return "medium"
            else:
                return "large"

    def optimize_config_for_audio(
        self, audio_characteristics: Dict[str, Any], priority: str = "balanced"
    ) -> ModelConfig:
        quality_score = audio_characteristics.get("quality_score", 75)
        snr_estimate = audio_characteristics.get("snr_estimate", 15)
        duration = audio_characteristics.get("duration", 60)

        if priority == "accuracy":
            config = ModelConfig.for_high_accuracy()
        elif priority == "speed":
            config = ModelConfig.for_speed()
        else:  # balanced
            config = ModelConfig()

        if quality_score < 60 or snr_estimate < 10:
            noisy_config = ModelConfig.for_noisy_audio()
            config.temperature = noisy_config.temperature
            config.beam_size = noisy_config.beam_size
            config.compression_ratio_threshold = (
                noisy_config.compression_ratio_threshold
            )
            config.no_speech_threshold = noisy_config.no_speech_threshold
            config.condition_on_previous_text = False

        if duration > 1800:
            config.beam_size = min(config.beam_size, 5)
            config.best_of = min(config.best_of, 5)
            config.patience = 1.0

        config.model_size = self.select_optimal_model_size(
            duration / 60, quality_score, priority
        )

        return config

    def create_domain_specific_prompt(self, domain: str) -> str:
        domain_prompts = {
            "medical": "Medical terminology and patient consultation discussion.",
            "legal": "Legal proceedings, contracts, and professional legal terminology.",
            "technical": "Technical discussion with industry-specific terminology.",
            "business": "Business meeting with professional terminology and names.",
            "education": "Educational content and academic discussion.",
            "podcast": "Podcast interview with natural conversation flow.",
            "meeting": "Business meeting with multiple speakers and professional discussion.",
            "interview": "Interview with questions and answers format.",
            "lecture": "Educational lecture with technical terminology.",
            "phone": "Phone call conversation with potential audio quality issues.",
        }

        return domain_prompts.get(domain, "")

    def optimize_for_multiple_speakers(self, estimated_speakers: int) -> Dict[str, Any]:
        if estimated_speakers <= 1:
            return {
                "condition_on_previous_text": True,
                "no_speech_threshold": 0.6,
                "compression_ratio_threshold": 2.4,
            }
        elif estimated_speakers <= 3:
            return {
                "condition_on_previous_text": False,  # Don't assume continuity
                "no_speech_threshold": 0.7,  # More conservative
                "compression_ratio_threshold": 2.0,  # Stricter
                "length_penalty": 0.9,  # Prefer shorter segments
            }
        else:  # Many speakers
            return {
                "condition_on_previous_text": False,
                "no_speech_threshold": 0.8,  # Very conservative
                "compression_ratio_threshold": 1.8,  # Very strict
                "length_penalty": 0.8,  # Prefer shorter segments
                "patience": 1.5,  # More patience for complex audio
            }

    def monitor_performance(
        self,
        config: ModelConfig,
        processing_time: float,
        audio_duration: float,
        quality_metrics: Dict[str, float],
    ) -> None:
        performance_entry = {
            "timestamp": time.time(),
            "config": config.__dict__,
            "processing_time": processing_time,
            "audio_duration": audio_duration,
            "efficiency_ratio": audio_duration / processing_time,
            "quality_metrics": quality_metrics,
        }

        self.performance_history.append(performance_entry)

        # Keep only recent history (last 100 entries)
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]

        self._update_optimal_configs()

    def _update_optimal_configs(self) -> None:
        if len(self.performance_history) < 10:
            return

        recent_performance = self.performance_history[-20:]

        by_model_size = {}
        for entry in recent_performance:
            model_size = entry["config"]["model_size"]
            if model_size not in by_model_size:
                by_model_size[model_size] = []
            by_model_size[model_size].append(entry)

        for model_size, entries in by_model_size.items():
            if len(entries) >= 3:
                best_entry = max(
                    entries,
                    key=lambda x: x["efficiency_ratio"]
                    * np.mean(list(x["quality_metrics"].values())),
                )

                self.optimal_configs[model_size] = best_entry["config"]

    def get_memory_optimized_config(self, available_memory_gb: float) -> ModelConfig:
        config = ModelConfig()

        if available_memory_gb < 4:
            config.model_size = "tiny"
            config.fp16 = True
            config.beam_size = 1
            config.best_of = 1
        elif available_memory_gb < 8:
            config.model_size = "base"
            config.fp16 = True
            config.beam_size = 3
            config.best_of = 3
        elif available_memory_gb < 16:
            config.model_size = "small"
            config.beam_size = 5
            config.best_of = 5
        else:
            config.model_size = "medium"
            config.beam_size = 8
            config.best_of = 8

        return config

    def estimate_processing_time(
        self, audio_duration_minutes: float, model_size: str, quality_score: float
    ) -> float:
        model_multipliers = {
            "tiny": 0.1,
            "base": 0.3,
            "small": 0.8,
            "medium": 2.0,
            "large": 4.0,
        }

        base_multiplier = model_multipliers.get(model_size, 1.0)

        quality_multiplier = 1.0 + (100 - quality_score) / 200

        audio_seconds = audio_duration_minutes * 60

        estimated_seconds = audio_seconds * base_multiplier * quality_multiplier

        return estimated_seconds
