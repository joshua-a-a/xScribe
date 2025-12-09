from __future__ import annotations

import pytest

from src.core.subtitle_generator import SubtitleGenerator
from src.models.transcription_result import (
    TranscriptionResult,
    TranscriptionSegment,
)


@pytest.fixture
def sample_result(tmp_path) -> TranscriptionResult:
    segments = [
        TranscriptionSegment(
            start=0.0,
            end=1.5,
            text="Hello world",
            confidence=0.92,
            speaker="Speaker 1",
        ),
        TranscriptionSegment(
            start=1.6,
            end=3.2,
            text="This is a modular xScribe test",
            confidence=0.88,
            speaker="Speaker 2",
        ),
    ]

    return TranscriptionResult(
        segments=segments,
        language="en",
        language_probability=0.99,
        duration=3.2,
        processing_time=0.6,
        model_used="tiny",
        file_path=tmp_path / "fixture.wav",
        metadata={"test": True},
    )


@pytest.fixture
def sample_segment(sample_result: TranscriptionResult) -> TranscriptionSegment:
    return sample_result.segments[0]


def test_transcription_result_to_dict_roundtrip(sample_result: TranscriptionResult):
    serialized = sample_result.to_dict()
    restored = TranscriptionResult.from_dict(serialized)

    assert restored.word_count == sample_result.word_count
    assert restored.metadata["test"] is True
    assert len(restored.segments) == 2
    assert restored.segments[1].speaker == "Speaker 2"


def test_transcription_result_helpers(sample_result: TranscriptionResult):
    assert sample_result.full_text.startswith("Hello world")
    assert sample_result.word_count > 4
    assert sample_result.get_unique_speakers() == ["Speaker 1", "Speaker 2"]


def test_subtitle_generator_outputs_supported_formats(
    sample_result: TranscriptionResult,
):
    generator = SubtitleGenerator()

    srt = generator.generate_subtitles(sample_result, "srt")
    assert "Hello world" in srt
    assert "00:00:00,000" in srt

    vtt = generator.generate_subtitles(sample_result, "vtt")
    assert vtt.startswith("WEBVTT")
    assert "This is a modular" in vtt


def test_transcription_result_rejects_empty_segments():
    with pytest.raises(ValueError):
        TranscriptionResult(
            segments=[],
            language="en",
            language_probability=0.9,
            duration=1.0,
            processing_time=0.1,
            model_used="tiny",
        )


@pytest.mark.parametrize("prob", [-0.1, 1.1])
def test_language_probability_out_of_bounds(prob, sample_segment):
    with pytest.raises(ValueError):
        TranscriptionResult(
            segments=[sample_segment],
            language="en",
            language_probability=prob,
            duration=1.0,
            processing_time=0.1,
            model_used="tiny",
        )


def test_average_confidence_can_be_none(sample_result):
    for seg in sample_result.segments:
        seg.confidence = None
    assert sample_result.average_confidence is None


def test_get_segments_by_speaker(sample_result):
    s1 = sample_result.get_segments_by_speaker("Speaker 1")
    assert len(s1) == 1
    assert s1[0].text == "Hello world"
