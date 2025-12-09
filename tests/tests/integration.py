"""Integration tests for xScribe transcription pipeline.

End-to-end tests that verify real transcription and subtitle generation
using actual fixtures. Requires ffmpeg and whisper to be installed.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from src.core.subtitle_generator import SubtitleGenerator
from src.core.transcription_service import EnhancedTranscriptionService
from src.models.transcription_result import TranscriptionResult

# ---------------------------------------------------------------------------
# External dependency checks
# ---------------------------------------------------------------------------
HAS_FFMPEG = shutil.which("ffmpeg") is not None

try:
    import whisper  # type: ignore

    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False


# ---------------------------------------------------------------------------
# WER helper (self-contained for this module)
# ---------------------------------------------------------------------------
def _wer(reference: str, hypothesis: str) -> float:
    ref_tokens = reference.lower().split()
    hyp_tokens = hypothesis.lower().split()

    if not ref_tokens:
        return 0.0 if not hyp_tokens else 1.0

    dp = [[0] * (len(hyp_tokens) + 1) for _ in range(len(ref_tokens) + 1)]

    for i in range(len(ref_tokens) + 1):
        dp[i][0] = i
    for j in range(len(hyp_tokens) + 1):
        dp[0][j] = j

    for i in range(1, len(ref_tokens) + 1):
        for j in range(1, len(hyp_tokens) + 1):
            cost = 0 if ref_tokens[i - 1] == hyp_tokens[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,  # deletion
                dp[i][j - 1] + 1,  # insertion
                dp[i - 1][j - 1] + cost,  # substitution
            )

    return dp[-1][-1] / len(ref_tokens)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def fixtures_root() -> Path:
    # tests/tests/integration.py → parent = tests/tests, parents[1] = tests
    return Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def sample_video_path(fixtures_root: Path) -> Path:
    return fixtures_root / "aud-vid" / "IMG_4589.MOV"


@pytest.fixture
def expected_transcript_text(fixtures_root: Path) -> str:
    """Expected transcript text from fixture file.

    The fixture file has a report format with headers; we extract
    just the transcription text between the TRANSCRIPTION markers.
    """
    txt_path = fixtures_root / "trnscrp" / "IMG_4589_transcript.txt"
    content = txt_path.read_text(encoding="utf-8")

    # Extract text between TRANSCRIPTION markers
    marker = "TRANSCRIPTION:"
    if marker in content:
        # Find start after the marker line and separator
        start_idx = content.find(marker)
        after_marker = content[start_idx:]
        lines = after_marker.split("\n")

        # Skip header lines (marker, separator, empty)
        transcript_lines = []
        in_transcript = False
        for line in lines[1:]:  # Skip the TRANSCRIPTION: line
            if line.startswith("=" * 10):
                if in_transcript:
                    break
                in_transcript = True
                continue
            if in_transcript and line.strip():
                transcript_lines.append(line.strip())

        return " ".join(transcript_lines)

    return content.strip()


@pytest.fixture
def expected_transcript_json(fixtures_root: Path) -> dict:
    """Expected transcript JSON from fixture file (optional)."""
    json_path = fixtures_root / "trnscrp" / "IMG_4589_transcript.json"
    if not json_path.exists():
        pytest.skip("JSON transcript fixture not present")
    return json.loads(json_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------
@pytest.mark.integration
@pytest.mark.skipif(
    not (HAS_FFMPEG and HAS_WHISPER),
    reason="Integration test requires ffmpeg and whisper installed",
)
def test_transcription_pipeline_end_to_end(
    sample_video_path: Path,
    expected_transcript_text: str,
    tmp_path: Path,
):
    # Skip if fixture file doesn't exist
    if not sample_video_path.exists():
        pytest.skip(f"Fixture video not found: {sample_video_path}")

    # Initialize service with tiny model for speed
    service = EnhancedTranscriptionService(
        model_size="tiny",
        enable_audio_enhancement=False,  # Skip for speed
        enable_speaker_detection=False,
    )

    result = service.transcribe_file(str(sample_video_path))

    assert isinstance(result, TranscriptionResult)
    assert result.segments, "Expected at least one segment"
    assert result.duration > 0, "Duration should be positive"
    assert result.word_count > 0, "Should have transcribed some words"

    wer = _wer(expected_transcript_text, result.full_text)

    assert wer < 0.40, f"WER {wer:.2f} exceeds threshold 0.40"

    generator = SubtitleGenerator()

    srt = generator.generate_subtitles(result, "srt")
    vtt = generator.generate_subtitles(result, "vtt")

    assert " --> " in srt, "SRT should contain timestamp arrows"
    assert " --> " in vtt, "VTT should contain timestamp arrows"
    assert vtt.startswith("WEBVTT"), "VTT should start with WEBVTT header"

    # Sanity: some expected words should appear in output
    lower_srt = srt.lower()
    lower_text = result.full_text.lower()
    found_match = False

    for token in expected_transcript_text.lower().split()[:10]:
        if len(token) > 3:  # Skip tiny words
            if token in lower_srt or token in lower_text:
                found_match = True
                break

    assert found_match, "Expected at least one keyword from transcript in output"


@pytest.mark.integration
@pytest.mark.skipif(
    not (HAS_FFMPEG and HAS_WHISPER),
    reason="Integration test requires ffmpeg and whisper installed",
)
def test_transcription_result_serialization_roundtrip(
    sample_video_path: Path,
):
    if not sample_video_path.exists():
        pytest.skip(f"Fixture video not found: {sample_video_path}")

    service = EnhancedTranscriptionService(
        model_size="tiny",
        enable_audio_enhancement=False,
        enable_speaker_detection=False,
    )

    result = service.transcribe_file(str(sample_video_path))

    result_dict = result.to_dict()
    assert isinstance(result_dict, dict)
    assert "segments" in result_dict

    restored = TranscriptionResult.from_dict(result_dict)

    assert restored.full_text == result.full_text
    assert restored.word_count == result.word_count
    assert len(restored.segments) == len(result.segments)
