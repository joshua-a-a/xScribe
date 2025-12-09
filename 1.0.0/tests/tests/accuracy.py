from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.core.text_processor import TextPostProcessor


@dataclass
class WerScenario:
    reference: str
    raw_transcript: str


def _calculate_wer(reference: str, hypothesis: str) -> float:
    ref_tokens = reference.lower().split()
    hyp_tokens = hypothesis.lower().split()

    # Reference has no words: WER is 0 only if hypothesis also empty,
    # otherwise treat as full error
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


@pytest.mark.parametrize(
    "scenario",
    [
        WerScenario(
            reference="We don't know if it's going to be a lot harder.",
            raw_transcript="we dont know if its going to be alot harder.",
        ),
        WerScenario(
            reference="AI teams confirmed the API is ready by 4 p.m.",
            raw_transcript="a i teams confirmed the a p i is ready by four p m",
        ),
    ],
)
def test_text_post_processor_improves_word_error_rate(scenario: WerScenario):
    processor = TextPostProcessor()

    processed_text = processor.process_text(scenario.raw_transcript)

    raw_wer = _calculate_wer(scenario.reference, scenario.raw_transcript)
    processed_wer = _calculate_wer(scenario.reference, processed_text)

    assert processed_wer <= raw_wer

    # Text should not remain identical after processing
    assert processed_text.strip() != scenario.raw_transcript.strip()


@pytest.mark.parametrize(
    "reference,hypothesis,expected",
    [
        # perfect match
        ("hello world", "hello world", 0.0),
        # one deletion: 2 -> 1 word, distance = 1
        ("hello world", "hello", 1 / 2),
        # one insertion: 1 -> 2 words, distance = 1
        ("hello", "hello world", 1.0),
        # one substitution out of 3
        ("a b c", "a x c", 1 / 3),
        # both empty
        ("", "", 0.0),
        # empty reference, non-empty hypothesis -> full error
        ("", "hello world", 1.0),
    ],
)
def test_calculate_wer_basic_cases(reference: str, hypothesis: str, expected: float):
    wer = _calculate_wer(reference, hypothesis)
    assert wer == pytest.approx(expected)
