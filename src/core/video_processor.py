import logging
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class VideoProcessor:
    SUPPORTED_VIDEO_FORMATS = {
        ".mp4",
        ".m4v",
        ".mov",
        ".avi",
        ".mkv",
        ".webm",
        ".flv",
        ".wmv",
        ".mpg",
        ".mpeg",
        ".3gp",
        ".ogv",
        ".vob",
        ".mts",
        ".m2ts",
        ".ts",
        ".divx",
        ".xvid",
        ".asf",
        ".rm",
        ".rmvb",
    }

    def __init__(self, temp_dir: Optional[Path] = None):
        self.temp_dir = temp_dir or Path(tempfile.gettempdir())
        self.temp_files = []

        self._check_ffmpeg()

    def _get_ffmpeg_path(self) -> str:
        if getattr(sys, "frozen", False) and sys.platform == "darwin":
            executable_dir = Path(sys.executable).parent
            resources_dir = executable_dir.parent / "Resources"
            bundled_ffmpeg = resources_dir / "bin" / "ffmpeg"

            logger.info("   Bundled app detected")
            logger.info(f"   Executable: {sys.executable}")
            logger.info(f"   Resources dir: {resources_dir}")
            logger.info(f"   Looking for ffmpeg at: {bundled_ffmpeg}")
            logger.info(f"   Exists: {bundled_ffmpeg.exists()}")

            if bundled_ffmpeg.exists():
                logger.info(f"✅ Using bundled ffmpeg: {bundled_ffmpeg}")
                return str(bundled_ffmpeg)
            else:
                logger.error(f"❌ Bundled ffmpeg not found at: {bundled_ffmpeg}")

        dev_ffmpeg = Path(__file__).parent.parent.parent / "bin" / "ffmpeg"
        logger.info(f"🔍 Checking development ffmpeg: {dev_ffmpeg}")
        if dev_ffmpeg.exists():
            logger.info(f"✅ Using development ffmpeg: {dev_ffmpeg}")
            return str(dev_ffmpeg)

        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg:
            logger.info(f"✅ Using system ffmpeg: {system_ffmpeg}")
            return system_ffmpeg

        logger.error("❌ ffmpeg not found in any location!")
        return None

    def _check_ffmpeg(self) -> bool:
        ffmpeg_path = self._get_ffmpeg_path()
        if not ffmpeg_path:
            raise RuntimeError(
                "ffmpeg not found. Please install ffmpeg:\n"
                "  macOS: brew install ffmpeg\n"
                "  Ubuntu: sudo apt install ffmpeg\n"
                "  Windows: Download from https://ffmpeg.org"
            )

        self.ffmpeg_path = ffmpeg_path
        logger.info(f"ffmpeg ready at: {ffmpeg_path}")
        return True

    def is_video_file(self, file_path: str) -> bool:
        path = Path(file_path)
        return path.suffix.lower() in self.SUPPORTED_VIDEO_FORMATS

    def extract_audio(
        self, video_path: str, output_format: str = "wav", sample_rate: int = 16000
    ) -> str:
        video_path_obj = Path(video_path)

        if not video_path_obj.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        if not self.is_video_file(video_path):
            raise ValueError(
                f"Unsupported video format: {video_path_obj.suffix}\n"
                f"Supported formats: {', '.join(sorted(self.SUPPORTED_VIDEO_FORMATS))}"
            )

        temp_audio = self.temp_dir / f"{video_path_obj.stem}_audio.{output_format}"

        try:
            logger.info(f"Extracting audio from video: {video_path_obj.name}")
            logger.info(f"Output: {temp_audio}")

            cmd = [
                self.ffmpeg_path,
                "-i",
                str(video_path_obj),
                "-vn",
                "-acodec",
                "pcm_s16le" if output_format == "wav" else "libmp3lame",
                "-ar",
                str(sample_rate),
                "-ac",
                "1",
                "-y",
                str(temp_audio),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode != 0:
                logger.error(f"ffmpeg error: {result.stderr}")
                raise RuntimeError(f"Audio extraction failed: {result.stderr}")

            if not temp_audio.exists():
                raise RuntimeError("Audio extraction produced no output file")

            self.temp_files.append(temp_audio)

            logger.info(f"Audio extracted successfully: {temp_audio.name}")
            return str(temp_audio)

        except subprocess.TimeoutExpired:
            raise RuntimeError("Audio extraction timed out (>5 minutes)")
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            if temp_audio.exists():
                temp_audio.unlink()
            raise RuntimeError(f"Failed to extract audio: {str(e)}")

    def get_video_info(self, video_path: str) -> dict:
        try:
            ffprobe_path = str(Path(self.ffmpeg_path).parent / "ffprobe")
            if not Path(ffprobe_path).exists():
                ffprobe_path = shutil.which("ffprobe") or "ffprobe"

            cmd = [
                ffprobe_path,
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(video_path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                import json

                info = json.loads(result.stdout)

                # Extract useful information
                format_info = info.get("format", {})
                duration = float(format_info.get("duration", 0))
                size = int(format_info.get("size", 0))

                # Find audio stream
                audio_stream = None
                for stream in info.get("streams", []):
                    if stream.get("codec_type") == "audio":
                        audio_stream = stream
                        break

                return {
                    "duration": duration,
                    "duration_formatted": f"{int(duration // 60)}m {int(duration % 60)}s",
                    "size_mb": size / (1024 * 1024),
                    "format": format_info.get("format_name", "unknown"),
                    "has_audio": audio_stream is not None,
                    "audio_codec": audio_stream.get("codec_name")
                    if audio_stream
                    else None,
                    "audio_sample_rate": audio_stream.get("sample_rate")
                    if audio_stream
                    else None,
                }
            else:
                logger.warning(f"Could not get video info: {result.stderr}")
                return {}

        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return {}

    def cleanup(self):
        for temp_file in self.temp_files:
            try:
                if Path(temp_file).exists():
                    Path(temp_file).unlink()
                    logger.debug(f"Cleaned up temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up {temp_file}: {e}")

        self.temp_files.clear()

    def __del__(self):
        self.cleanup()
