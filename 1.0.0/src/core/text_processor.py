import logging
import re
import string
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PostProcessingConfig:
    fix_capitalization: bool = True
    fix_punctuation: bool = True
    normalize_numbers: bool = True
    fix_common_mistakes: bool = True
    enhance_formatting: bool = True
    fix_speaker_labels: bool = True
    remove_disfluencies: bool = False
    normalize_whitespace: bool = True
    apply_domain_corrections: bool = True


class TextPostProcessor:
    def __init__(self, config: Optional[PostProcessingConfig] = None):
        self.config = config or PostProcessingConfig()
        self._load_correction_dictionaries()
        self._compile_regex_patterns()

    def _load_correction_dictionaries(self):
        self.common_corrections = {
            " dont ": " don't ",
            " cant ": " can't ",
            " wont ": " won't ",
            " isnt ": " isn't ",
            " arent ": " aren't ",
            " wasnt ": " wasn't ",
            " werent ": " weren't ",
            " hasnt ": " hasn't ",
            " havent ": " haven't ",
            " hadnt ": " hadn't ",
            " shouldnt ": " shouldn't ",
            " couldnt ": " couldn't ",
            " wouldnt ": " wouldn't ",
            " mustnt ": " mustn't ",
            " neednt ": " needn't ",
            " daren't ": " daren't ",
            " there ": " their ",  # Context-dependent
            " your ": " you're ",  # Context-dependent
            " its ": " it's ",  # Context-dependent
            " alot ": " a lot ",
            " incase ": " in case ",
            " eachother ": " each other ",
            " everyday ": " every day ",  # Context-dependent
            " anyone ": " any one ",  # Context-dependent
            " cannot ": " can not ",  # Style preference
            " A I ": " AI ",
            " I T ": " IT ",
            " U I ": " UI ",
            " U X ": " UX ",
            " A P I ": " API ",
            " C E O ": " CEO ",
            " C T O ": " CTO ",
            " H R ": " HR ",
            " P R ": " PR ",
            " dollar ": " $ ",
            " dollars ": " dollars ",
            " percent ": " % ",
            " per cent ": " % ",
        }

        self.domain_corrections = {
            "medical": {
                " mg ": " mg ",
                " ml ": " mL ",
                " ecg ": " ECG ",
                " mri ": " MRI ",
                " ct scan": " CT scan",
                " x ray ": " X-ray ",
                " bp ": " BP ",
                " hr ": " HR ",
                "patient ": "patient ",
                "diagnosis": "diagnosis",
                "prescription": "prescription",
                "treatment": "treatment",
            },
            "legal": {
                "plaintiff": "plaintiff",
                "defendant": "defendant",
                "attorney": "attorney",
                "contract": "contract",
                "agreement": "agreement",
                "clause": "clause",
                "liable": "liable",
                "litigation": "litigation",
                "jurisdiction": "jurisdiction",
            },
            "technical": {
                "algorithm": "algorithm",
                "database": "database",
                "software": "software",
                "hardware": "hardware",
                "network": "network",
                "server": "server",
                "client": "client",
                "interface": "interface",
                "framework": "framework",
                "deployment": "deployment",
            },
        }

        self.disfluencies = {
            "um",
            "uh",
            "er",
            "ah",
            "like",
            "you know",
            "sort of",
            "kind of",
            "i mean",
            "basically",
            "actually",
            "literally",
            "so",
            "well",
            "right",
            "okay",
            "alright",
            "yeah",
            "yes",
            "mm-hmm",
            "uh-huh",
        }

    def _compile_regex_patterns(self):
        self.sentence_end_pattern = re.compile(r"[.!?]+")

        self.multiple_spaces_pattern = re.compile(r"\s{2,}")

        self.number_patterns = {
            "currency": re.compile(
                r"\b(\d+)\s+(dollars?|cents?|pounds?|euros?)\b", re.IGNORECASE
            ),
            "percentage": re.compile(r"\b(\d+(?:\.\d+)?)\s+percent\b", re.IGNORECASE),
            "ordinal": re.compile(r"\b(\d+)(st|nd|rd|th)\b"),
            "decimal": re.compile(r"\b(\d+)\s+point\s+(\d+)\b"),
            "fraction": re.compile(
                r"\b(one|two|three|four|five|six|seven|eight|nine)\s+(half|third|fourth|fifth|sixth|seventh|eighth|ninth)\b"
            ),
        }

        self.time_patterns = {
            "time_12h": re.compile(
                r"\b(\d{1,2})\s+(o\'?clock|a\.?m\.?|p\.?m\.?)\b", re.IGNORECASE
            ),
            "time_24h": re.compile(r"\b(\d{1,2}):(\d{2})\b"),
            "duration": re.compile(
                r"\b(\d+)\s+(hours?|minutes?|seconds?)\b", re.IGNORECASE
            ),
        }

        self.punctuation_patterns = {
            "comma_pause": re.compile(r"\s+,\s+"),
            "period_end": re.compile(r"\s+\.\s*$"),
            "question_tone": re.compile(r"\s+\?\s*$"),
            "exclamation_emphasis": re.compile(r"\s+!\s*$"),
        }

    def process_text(self, text: str, domain: Optional[str] = None) -> str:
        if not text or not text.strip():
            return ""

        logger.info(f"🔤 Processing text: {len(text)} characters")

        processed_text = text

        if self.config.normalize_whitespace:
            processed_text = self._normalize_whitespace(processed_text)

        if self.config.fix_common_mistakes:
            processed_text = self._fix_common_mistakes(processed_text)

        if self.config.apply_domain_corrections and domain:
            processed_text = self._apply_domain_corrections(processed_text, domain)

        if self.config.normalize_numbers:
            processed_text = self._normalize_numbers(processed_text)

        if self.config.fix_capitalization:
            processed_text = self._fix_capitalization(processed_text)

        if self.config.fix_punctuation:
            processed_text = self._enhance_punctuation(processed_text)

        if self.config.remove_disfluencies:
            processed_text = self._remove_disfluencies(processed_text)

        if self.config.enhance_formatting:
            processed_text = self._enhance_formatting(processed_text)

        logger.info(f"✅ Text processed: {len(processed_text)} characters")
        return processed_text.strip()

    def _normalize_whitespace(self, text: str) -> str:
        text = self.multiple_spaces_pattern.sub(" ", text)

        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = re.sub(r"\n\s+", "\n", text)

        return text.strip()

    def _fix_common_mistakes(self, text: str) -> str:
        for mistake, correction in self.common_corrections.items():
            text = text.replace(mistake.lower(), correction.lower())

        return text

    def _apply_domain_corrections(self, text: str, domain: str) -> str:
        if domain in self.domain_corrections:
            corrections = self.domain_corrections[domain]
            text_lower = text.lower()

            for term, correct_form in corrections.items():
                pattern = re.compile(r"\b" + re.escape(term.lower()) + r"\b")
                text = pattern.sub(correct_form, text_lower)

        return text

    def _normalize_numbers(self, text: str) -> str:
        text = self.number_patterns["currency"].sub(r"$\1", text)

        text = self.number_patterns["percentage"].sub(r"\1%", text)

        text = self.number_patterns["decimal"].sub(r"\1.\2", text)

        # Written numbers to digits (basic cases)
        number_words = {
            "zero": "0",
            "one": "1",
            "two": "2",
            "three": "3",
            "four": "4",
            "five": "5",
            "six": "6",
            "seven": "7",
            "eight": "8",
            "nine": "9",
            "ten": "10",
            "eleven": "11",
            "twelve": "12",
            "thirteen": "13",
            "fourteen": "14",
            "fifteen": "15",
            "sixteen": "16",
            "seventeen": "17",
            "eighteen": "18",
            "nineteen": "19",
            "twenty": "20",
            "thirty": "30",
            "forty": "40",
            "fifty": "50",
            "sixty": "60",
            "seventy": "70",
            "eighty": "80",
            "ninety": "90",
            "hundred": "100",
            "thousand": "1000",
        }

        for word, digit in number_words.items():
            text = re.sub(r"\b" + word + r"\b", digit, text, flags=re.IGNORECASE)

        return text

    def _fix_capitalization(self, text: str) -> str:
        sentences = self.sentence_end_pattern.split(text)
        capitalized_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                sentence = (
                    sentence[0].upper() + sentence[1:]
                    if len(sentence) > 1
                    else sentence.upper()
                )

                sentence = re.sub(r"\bi\b", "I", sentence)

                days = [
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday",
                ]
                for day in days:
                    sentence = re.sub(
                        r"\b" + day + r"\b",
                        day.capitalize(),
                        sentence,
                        flags=re.IGNORECASE,
                    )

                months = [
                    "january",
                    "february",
                    "march",
                    "april",
                    "may",
                    "june",
                    "july",
                    "august",
                    "september",
                    "october",
                    "november",
                    "december",
                ]
                for month in months:
                    sentence = re.sub(
                        r"\b" + month + r"\b",
                        month.capitalize(),
                        sentence,
                        flags=re.IGNORECASE,
                    )

            capitalized_sentences.append(sentence)

        return ". ".join(capitalized_sentences)

    def _enhance_punctuation(self, text: str) -> str:
        sentences = text.split("\n")
        enhanced_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and sentence[-1] not in ".!?":
                sentence += "."
            enhanced_sentences.append(sentence)

        text = re.sub(r"\s*,\s*", ", ", "\n".join(enhanced_sentences))

        text = re.sub(r"\s*\.\s*", ". ", text)

        text = re.sub(r"\s*\?\s*", "? ", text)

        text = re.sub(r"\s*!\s*", "! ", text)

        return text

    def _remove_disfluencies(self, text: str) -> str:
        words = text.split()
        filtered_words = []

        i = 0
        while i < len(words):
            word = words[i].lower().strip(string.punctuation)

            if i < len(words) - 1:
                two_word = f"{word} {words[i + 1].lower().strip(string.punctuation)}"
                if two_word in self.disfluencies:
                    i += 2
                    continue

            if word not in self.disfluencies:
                filtered_words.append(words[i])

            i += 1

        return " ".join(filtered_words)

    def _enhance_formatting(self, text: str) -> str:
        text = re.sub(r"([.!?])\s*", r"\1 ", text)
        text = re.sub(r"\s+([.!?])", r"\1", text)

        text = re.sub(r" +$", "", text, flags=re.MULTILINE)

        text = re.sub(r" +", " ", text)

        return text.strip()

    def get_confidence_score(self, original_text: str, processed_text: str) -> float:
        if not original_text:
            return 0.0

        original_words = set(original_text.lower().split())
        processed_words = set(processed_text.lower().split())

        intersection = len(original_words & processed_words)
        union = len(original_words | processed_words)
        similarity = intersection / union if union > 0 else 0.0

        length_ratio = min(len(processed_text), len(original_text)) / max(
            len(processed_text), len(original_text)
        )

        confidence = (similarity * 0.7) + (length_ratio * 0.3)

        return confidence

    def batch_process(
        self, segments: List[Dict[str, Any]], domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        processed_segments = []

        for segment in segments:
            if "text" in segment:
                original_text = segment["text"]
                processed_text = self.process_text(original_text, domain)

                confidence_score = self.get_confidence_score(
                    original_text, processed_text
                )

                processed_segment = segment.copy()
                processed_segment["text"] = processed_text
                processed_segment["processing_confidence"] = confidence_score
                processed_segment["original_text"] = original_text

                processed_segments.append(processed_segment)
            else:
                processed_segments.append(segment)

        return processed_segments
