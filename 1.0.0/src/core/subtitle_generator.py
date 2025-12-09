import logging
import re
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models.transcription_result import TranscriptionResult, TranscriptionSegment

logger = logging.getLogger(__name__)


@dataclass
class WordTimestamp:
    word: str
    start: float
    end: float
    confidence: Optional[float] = None

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class SubtitleSegment:
    start: float
    end: float
    text: str
    words: List[WordTimestamp]
    confidence: Optional[float] = None
    speaker: Optional[str] = None

    def format_time_srt(self, time_seconds: float) -> str:
        td = timedelta(seconds=time_seconds)
        hours = int(td.total_seconds() // 3600)
        minutes = int((td.total_seconds() % 3600) // 60)
        seconds = int(td.total_seconds() % 60)
        milliseconds = int((td.total_seconds() % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def format_time_vtt(self, time_seconds: float) -> str:
        return self.format_time_srt(time_seconds).replace(",", ".")

    def to_srt(self, index: int) -> str:
        start_time = self.format_time_srt(self.start)
        end_time = self.format_time_srt(self.end)
        return f"{index}\n{start_time} --> {end_time}\n{self.text.strip()}\n"

    def to_vtt(self) -> str:
        start_time = self.format_time_vtt(self.start)
        end_time = self.format_time_vtt(self.end)
        return f"{start_time} --> {end_time}\n{self.text.strip()}\n"


class SubtitleGenerator:
    def __init__(
        self,
        max_chars_per_line: int = 42,
        max_lines_per_subtitle: int = 2,
        min_duration_seconds: float = 1.0,
        max_duration_seconds: float = 7.0,
        gap_threshold_seconds: float = 0.3,
    ):
        self.max_chars_per_line = max_chars_per_line
        self.max_lines_per_subtitle = max_lines_per_subtitle
        self.min_duration_seconds = min_duration_seconds
        self.max_duration_seconds = max_duration_seconds
        self.gap_threshold_seconds = gap_threshold_seconds

        logger.info(
            f"SubtitleGenerator initialized with {max_chars_per_line} chars/line"
        )

    def enhance_segments_with_word_timing(
        self,
        transcription_result: TranscriptionResult,
        word_timestamps: Optional[List[Dict[str, Any]]] = None,
    ) -> List[SubtitleSegment]:
        enhanced_segments = []

        for segment in transcription_result.segments:
            words = []
            if word_timestamps:
                segment_words = self._extract_segment_words(segment, word_timestamps)
                words = [
                    WordTimestamp(
                        word=word["word"].strip(),
                        start=word["start"],
                        end=word["end"],
                        confidence=word.get("confidence"),
                    )
                    for word in segment_words
                    if word["word"].strip()
                ]
            else:
                words = self._estimate_word_timing(segment)

            enhanced_segment = SubtitleSegment(
                start=segment.start,
                end=segment.end,
                text=segment.text,
                words=words,
                confidence=segment.confidence,
                speaker=segment.speaker,
            )

            enhanced_segments.append(enhanced_segment)

        return enhanced_segments

    def _extract_segment_words(
        self, segment: TranscriptionSegment, word_timestamps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        segment_words = []

        for word_data in word_timestamps:
            word_start = word_data.get("start", 0)
            word_end = word_data.get("end", 0)

            if word_start >= segment.start - 0.1 and word_end <= segment.end + 0.1:
                segment_words.append(word_data)

        return segment_words

    def _estimate_word_timing(
        self, segment: TranscriptionSegment
    ) -> List[WordTimestamp]:
        words = segment.text.strip().split()
        if not words:
            return []

        segment_duration = segment.end - segment.start

        time_per_word = segment_duration / len(words)

        word_timestamps = []
        current_time = segment.start

        for word in words:
            word_duration = time_per_word * (0.7 + 0.6 * len(word) / 10)
            word_duration = min(
                word_duration, segment_duration * 0.5
            )  # Cap at 50% of segment

            word_timestamps.append(
                WordTimestamp(
                    word=word,
                    start=current_time,
                    end=current_time + word_duration,
                    confidence=segment.confidence,
                )
            )

            current_time += word_duration

        return word_timestamps

    def optimize_subtitle_timing(
        self, segments: List[SubtitleSegment]
    ) -> List[SubtitleSegment]:
        if not segments:
            return segments

        optimized = []

        for i, segment in enumerate(segments):
            duration = segment.end - segment.start
            if duration < self.min_duration_seconds:
                segment.end = segment.start + self.min_duration_seconds

            if duration > self.max_duration_seconds:
                pass

            if i < len(segments) - 1:
                next_segment = segments[i + 1]
                gap = next_segment.start - segment.end

                if gap < self.gap_threshold_seconds:
                    midpoint = (segment.end + next_segment.start) / 2
                    segment.end = midpoint - (self.gap_threshold_seconds / 2)
                    next_segment.start = midpoint + (self.gap_threshold_seconds / 2)

            optimized.append(segment)

        return optimized

    def break_text_for_subtitles(self, text: str) -> List[str]:
        text = re.sub(r"\s+", " ", text.strip())

        if len(text) <= self.max_chars_per_line:
            return [text]

        lines = []
        words = text.split()
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()

            if len(test_line) <= self.max_chars_per_line:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    lines.append(word[: self.max_chars_per_line])
                    current_line = word[self.max_chars_per_line :]

                if len(lines) >= self.max_lines_per_subtitle:
                    break

        if current_line and len(lines) < self.max_lines_per_subtitle:
            lines.append(current_line)

        return lines[: self.max_lines_per_subtitle]

    def generate_srt(self, segments: List[SubtitleSegment]) -> str:
        srt_content = []

        for i, segment in enumerate(segments, 1):
            lines = self.break_text_for_subtitles(segment.text)
            formatted_text = "\n".join(lines)

            start_time = segment.format_time_srt(segment.start)
            end_time = segment.format_time_srt(segment.end)

            srt_entry = f"{i}\n{start_time} --> {end_time}\n{formatted_text}\n"
            srt_content.append(srt_entry)

        return "\n".join(srt_content)

    def generate_vtt(self, segments: List[SubtitleSegment]) -> str:
        vtt_content = ["WEBVTT", ""]

        for segment in segments:
            lines = self.break_text_for_subtitles(segment.text)
            formatted_text = "\n".join(lines)

            if segment.speaker:
                formatted_text = f"<v {segment.speaker}>{formatted_text}</v>"

            start_time = segment.format_time_vtt(segment.start)
            end_time = segment.format_time_vtt(segment.end)

            vtt_entry = f"{start_time} --> {end_time}\n{formatted_text}\n"
            vtt_content.append(vtt_entry)

        return "\n".join(vtt_content)

    def generate_subtitles(
        self,
        transcription_result: TranscriptionResult,
        format: str = "srt",
        word_timestamps: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        logger.info(
            f"🎬 Generating {format.upper()} subtitles from {len(transcription_result.segments)} segments"
        )

        enhanced_segments = self.enhance_segments_with_word_timing(
            transcription_result, word_timestamps
        )

        optimized_segments = self.optimize_subtitle_timing(enhanced_segments)

        if format.lower() == "srt":
            return self.generate_srt(optimized_segments)
        elif format.lower() == "vtt":
            return self.generate_vtt(optimized_segments)
        else:
            raise ValueError(f"Unsupported subtitle format: {format}")

    def save_subtitles(
        self,
        transcription_result: TranscriptionResult,
        output_path: str,
        format: str = "srt",
        word_timestamps: Optional[List[Dict[str, Any]]] = None,
    ):
        subtitles = self.generate_subtitles(
            transcription_result, format, word_timestamps
        )

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(subtitles)

        logger.info(f"Subtitles saved to: {output_file}")
