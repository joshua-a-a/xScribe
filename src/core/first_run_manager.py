import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class FirstRunManager:
    MODEL_SIZES = {
        "tiny": "75 MB",
        "base": "150 MB",
        "small": "500 MB",
        "medium": "1.5 GB",
        "large": "3 GB",
    }

    def __init__(self):
        self.config_path = Path.home() / "Library/Application Support/xScribe"
        self.config_file = self.config_path / "config.json"

        self.cache_dir = Path.home() / ".cache/whisper"

        self.config_path.mkdir(parents=True, exist_ok=True)

    def is_first_run(self) -> bool:
        return not self.config_file.exists()

    def get_config(self) -> dict:
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                return self._default_config()
        return self._default_config()

    def _default_config(self) -> dict:
        return {
            "first_run_complete": False,
            "version": "1.0.0",
            "setup_date": None,
            "models_downloaded": [],
            "default_model": "base",
            "privacy_consent": False,
        }

    def save_config(self, config: dict):
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise

    def complete_first_run(self):
        config = self.get_config()
        config["first_run_complete"] = True
        config["setup_date"] = datetime.now().isoformat()
        self.save_config(config)
        logger.info("First run setup completed")

    def is_model_downloaded(self, model_name: str) -> bool:
        try:
            model_file = self.cache_dir / f"{model_name}.pt"
            exists = model_file.exists()

            if exists:
                logger.debug(f"Model {model_name} found at {model_file}")
            else:
                logger.debug(f"Model {model_name} not found at {model_file}")

            return exists
        except Exception as e:
            logger.warning(f"Error checking model {model_name}: {e}")
            return False

    def get_downloaded_models(self) -> list:
        downloaded = []
        for model_name in ["tiny", "base", "small", "medium", "large"]:
            if self.is_model_downloaded(model_name):
                downloaded.append(model_name)
        return downloaded

    def download_model(self, model_name: str, progress_callback=None) -> bool:
        try:
            import whisper

            if progress_callback:
                progress_callback(
                    f"Downloading {model_name} model ({self.MODEL_SIZES.get(model_name, 'unknown size')})...",
                    10,
                )

            logger.info(f"Downloading Whisper {model_name} model...")

            model = whisper.load_model(model_name, download_root=str(self.cache_dir))

            if progress_callback:
                progress_callback(f"{model_name.capitalize()} model ready!", 100)

            config = self.get_config()
            if model_name not in config["models_downloaded"]:
                config["models_downloaded"].append(model_name)
                self.save_config(config)

            logger.info(f"Successfully downloaded {model_name} model")
            return True

        except Exception as e:
            logger.error(f"Failed to download {model_name} model: {e}")
            if progress_callback:
                progress_callback(f"Failed to download {model_name} model: {str(e)}", 0)
            return False

    def download_all_models(self, progress_callback=None) -> tuple[bool, list]:
        models_to_download = ["tiny", "base", "small", "medium"]
        failed_models = []
        total = len(models_to_download)

        for i, model_name in enumerate(models_to_download):
            try:
                if progress_callback:
                    overall_progress = int((i / total) * 100)
                    progress_callback(
                        f"Downloading {model_name} model ({self.MODEL_SIZES.get(model_name, 'unknown')})... ({i + 1}/{total})",
                        overall_progress,
                        i + 1,
                        total,
                    )

                logger.info(f"Downloading model {i + 1}/{total}: {model_name}")

                success = self.download_model(model_name)

                if not success:
                    failed_models.append(model_name)
                    logger.error(f"Failed to download {model_name}")
                else:
                    logger.info(f"Successfully downloaded {model_name}")

            except Exception as e:
                logger.error(f"Error downloading {model_name}: {e}")
                failed_models.append(model_name)

        if progress_callback:
            if not failed_models:
                progress_callback(
                    "All models downloaded successfully!", 100, total, total
                )
            else:
                progress_callback(
                    f"Download complete with {len(failed_models)} failures",
                    100,
                    total,
                    total,
                )

        all_successful = len(failed_models) == 0
        return all_successful, failed_models

    def get_welcome_message(self) -> str:
        return """
Welcome to xScribe!

The Solution to Private Audio & Video Transcription

Features:
• Transcribe audio and video files
• 100% offline - complete privacy
• Speaker identification
• Word level timestamps
• Supports 21 video formats + all major audio formats

First Time Setup:
Models are downloaded sp they are on demand when you want to use them.
We recommend starting with the 'tiny' (75 MB) or 'base' model (150 MB).

All processing is done locally on your Mac.
No internet required after model download.
No data ever leaves your computer.
        """.strip()

    def get_model_recommendation(self) -> dict:
        return {
            "model": "base",
            "reason": "Best balance of speed and accuracy for most users",
            "size": self.MODEL_SIZES["base"],
            "alternatives": {
                "tiny": "Fastest, good for clean audio (75 MB)",
                "small": "Better accuracy, still fast (500 MB)",
                "medium": "High accuracy, slower (1.5 GB)",
            },
        }

    def check_disk_space(self, model_name: str) -> tuple[bool, str]:
        import shutil

        required_mb = {
            "tiny": 75 + 500,
            "base": 150 + 500,
            "small": 500 + 500,
            "medium": 1500 + 500,
            "large": 3000 + 500,
        }

        try:
            stat = shutil.disk_usage(Path.home())
            free_mb = stat.free / (1024 * 1024)
            needed_mb = required_mb.get(model_name, 500)

            if free_mb < needed_mb:
                return (
                    False,
                    f"Insufficient disk space. Need {needed_mb}MB, have {free_mb:.0f}MB free",
                )

            return True, f"Sufficient space available ({free_mb:.0f}MB free)"

        except Exception as e:
            logger.error(f"Failed to check disk space: {e}")
            return True, "Could not verify disk space"

    def cleanup_old_models(self):
        if not self.cache_dir.exists():
            return

        try:
            model_files = list(self.cache_dir.glob("*.pt"))
            logger.info(f"Found {len(model_files)} model files in cache")

            for model_file in model_files:
                size_mb = model_file.stat().st_size / (1024 * 1024)
                logger.info(f"  {model_file.name}: {size_mb:.1f} MB")

        except Exception as e:
            logger.error(f"Failed to check model cache: {e}")
