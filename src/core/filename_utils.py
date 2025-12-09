import re
import unicodedata
from pathlib import Path
from typing import Optional


def sanitize_filename(
    filename: str, replacement: str = "_", max_length: int = 255
) -> str:
    filename = unicodedata.normalize("NFC", filename)

    forbidden_chars = r'[<>:"/\\|?*\x00-\x1f]'
    filename = re.sub(forbidden_chars, replacement, filename)

    if replacement:
        filename = re.sub(f"{re.escape(replacement)}+", replacement, filename)

    filename = filename.strip(". ")

    reserved_names = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }

    if filename.upper() in reserved_names:
        filename = f"{filename}{replacement}file"

    if not filename or filename == replacement:
        filename = "transcription"

    safe_length = max_length - 50
    if len(filename) > safe_length:
        filename = filename[:safe_length].rstrip(". ")

    return filename


def sanitize_path_component(path_str: str) -> str:
    return sanitize_filename(path_str, replacement="_")


def safe_filename_from_path(
    file_path: Optional[str], default: str = "transcription"
) -> str:
    if not file_path:
        return default

    try:
        # Extract stem (filename without extension)
        stem = Path(file_path).stem

        # Sanitize it
        safe_name = sanitize_filename(stem)

        # Return default if sanitization resulted in empty string
        return safe_name if safe_name else default

    except Exception:
        return default


def create_safe_output_path(
    base_dir: Path,
    original_filename: Optional[str],
    suffix: str = "_transcript",
    extension: str = ".txt",
) -> Path:
    safe_name = safe_filename_from_path(original_filename)

    output_filename = f"{safe_name}{suffix}{extension}"

    return base_dir / output_filename


def validate_output_path(file_path: Path) -> tuple[bool, str]:
    try:
        if len(str(file_path)) > 250:
            return False, f"Path too long: {len(str(file_path))} characters (max 250)"

        for part in file_path.parts:
            if len(part) > 255:
                return False, f"Path component too long: '{part}' ({len(part)} chars)"

        parent = file_path.parent
        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"Cannot create directory: {str(e)}"

        if not parent.is_dir():
            return False, f"Parent path exists but is not a directory: {parent}"

        return True, "Path is valid"

    except Exception as e:
        return False, f"Path validation error: {str(e)}"


# Common problematic filename examples and their safe versions
EXAMPLES = {
    "My Podcast: Episode #1 (2024)": "My_Podcast_Episode_1_2024",
    "Interview w/ CEO @ Startup": "Interview_w_CEO_Startup",
    "File <FINAL> [Version 2].mp3": "File_FINAL_Version_2",
    "Webinar 10/21/2025 - Q&A": "Webinar_10_21_2025_Q_A",
    "Recording | Team Meeting": "Recording_Team_Meeting",
    "Café Music & Ambience": "Café_Music_Ambience",
    "CON": "CON_file",  # Windows reserved name
    "   spaces.mp3   ": "spaces",  # Leading/trailing spaces removed
}
