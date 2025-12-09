import multiprocessing
import os
import sys

# Redirect Numba cache outside the signed bundle before any imports
os.environ["NUMBA_CACHE_DIR"] = os.path.join(os.path.expanduser("~"), ".cache", "numba")

# Configure multiprocessing for frozen macOS apps before anything else
if getattr(sys, "frozen", False) and sys.platform == "darwin":
    try:
        multiprocessing.set_start_method("spawn", force=True)
    except RuntimeError:
        pass  # Already set

    multiprocessing.set_executable(sys.executable)

# Call freeze_support before any multiprocessing work
if __name__ == "__main__":
    multiprocessing.freeze_support()

    _is_child_process = (
        any(arg.startswith("--multiprocessing") for arg in sys.argv)
        or "MP_MAIN_FILE" in os.environ
        or "_MP_FORK_LOGLEVEL_" in os.environ
        or any("resource_tracker" in arg for arg in sys.argv)
        or any("semaphore_tracker" in arg for arg in sys.argv)
        or any("from multiprocessing" in arg for arg in sys.argv)
    )

    if _is_child_process and getattr(sys, "frozen", False):
        sys.exit(0)

# Preload libsndfile before soundfile tries to dlopen inside the bundle
if getattr(sys, "frozen", False) and sys.platform == "darwin":
    import ctypes

    executable_dir = os.path.dirname(sys.executable)
    frameworks_dir = os.path.join(executable_dir, "..", "Frameworks")
    bundled_lib = os.path.join(frameworks_dir, "libsndfile.dylib")

    if os.path.exists(bundled_lib):
        try:
            ctypes.CDLL(bundled_lib, mode=ctypes.RTLD_GLOBAL)
        except Exception:
            pass  # Silently continue - child processes don't need verbose output

    resources_dir = os.path.join(executable_dir, "..", "Resources")
    ffmpeg_bin_dir = os.path.join(resources_dir, "bin")
    if os.path.exists(ffmpeg_bin_dir):
        os.environ["PATH"] = ffmpeg_bin_dir + os.pathsep + os.environ.get("PATH", "")

    libsndfile_path = os.path.join(frameworks_dir, "libsndfile.1.dylib")
    if os.path.exists(libsndfile_path):
        os.environ["LIBSNDFILE_LIB"] = libsndfile_path


def _setup_and_run():
    """Main application setup - only runs in the primary process."""
    import atexit
    import fcntl
    import logging
    import signal
    import traceback
    from datetime import datetime
    from pathlib import Path

    lock_dir = Path.home() / "Library" / "Application Support" / "xScribe"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_file = lock_dir / ".xscribe.lock"

    try:
        lock_fd = open(lock_file, "w")
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, OSError):
        print("xScribe is already running. Bringing existing window to front.")
        sys.exit(0)

    from src.gui.main_window import run_professional_gui

    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.append(current_dir)

    whisper_cache = Path.home() / ".cache" / "whisper"
    whisper_cache.mkdir(parents=True, exist_ok=True)
    os.environ["WHISPER_CACHE_DIR"] = str(whisper_cache)
    os.environ["XDG_CACHE_HOME"] = str(Path.home() / ".cache")

    if getattr(sys, "frozen", False):
        logs_dir = os.path.join(
            str(Path.home()), "Library", "Application Support", "xScribe", "logs"
        )
    else:
        logs_dir = os.path.join(current_dir, "logs")

    os.makedirs(logs_dir, exist_ok=True)

    log_file = os.path.join(
        logs_dir, f"xscribe_{datetime.now().strftime('%Y%m%d')}.log"
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    logger = logging.getLogger(__name__)

    _shutting_down = False

    def emergency_shutdown(signum=None, frame=None):
        """Emergency shutdown handler - called on crashes or signals"""
        nonlocal _shutting_down

        if _shutting_down:
            return
        _shutting_down = True

        if signum:
            logger.critical(f"EMERGENCY SHUTDOWN - Signal {signum} received")
        else:
            logger.info("Application shutdown initiated")

        logger.info("Attempting to save application state")

        try:
            from src.core.app_instance import AppInstanceManager

            manager = AppInstanceManager()
            manager.emergency_save_state()
        except Exception as e:
            logger.error(f"Emergency save failed: {e}")

        logger.info("=" * 60)
        logger.info("xScribe shutdown complete")
        logger.info("=" * 60)

        if signum:
            sys.exit(1)

    # Register signal handlers
    signal.signal(signal.SIGTERM, emergency_shutdown)
    signal.signal(signal.SIGINT, emergency_shutdown)
    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, emergency_shutdown)

    atexit.register(emergency_shutdown)

    logger.info("=" * 60)
    logger.info("xScribe Starting")
    logger.info("=" * 60)

    def check_first_run():
        """Handle first-run setup if needed"""
        from src.core.first_run_manager import FirstRunManager

        manager = FirstRunManager()

        if manager.is_first_run():
            logger.info("First run detected - setup will be shown in GUI")
            return True

        config = manager.get_config()
        logger.info(
            f"xScribe initialized (setup: {config.get('setup_date', 'unknown')})"
        )
        logger.info(f"Downloaded models: {config.get('models_downloaded', [])}")
        return False

    try:
        logger.info(f"Log file: {log_file}")
        logger.info("Crash recovery handlers registered")

        is_first_run = check_first_run()

        exit_code = run_professional_gui(is_first_run=is_first_run)
        logger.info("xScribe shutting down normally")
        sys.exit(exit_code)

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\nApplication interrupted by user")
        emergency_shutdown()
        sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error starting xScribe: {e}", exc_info=True)
        print(f"Error starting xScribe: {e}")
        traceback.print_exc()
        emergency_shutdown()
        sys.exit(1)


if __name__ == "__main__":
    _setup_and_run()
