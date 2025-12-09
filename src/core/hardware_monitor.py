import logging
import platform
from typing import Dict, Optional

import psutil

logger = logging.getLogger(__name__)


class HardwareMonitor:
    def __init__(self):
        self.system = platform.system()
        self.initial_cpu_freq = None
        self.warning_shown = False

        try:
            if hasattr(psutil, "cpu_freq"):
                freq = psutil.cpu_freq()
                if freq:
                    self.initial_cpu_freq = freq.current
        except Exception:
            pass

    def check_system_health(self) -> Dict[str, any]:
        status = {
            "healthy": True,
            "warnings": [],
            "cpu_percent": 0,
            "memory_percent": 0,
            "memory_available_gb": 0,
            "throttling_detected": False,
            "temperature_warning": False,
        }

        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            status["cpu_percent"] = cpu_percent

            if cpu_percent > 95:
                status["warnings"].append(f"CPU usage very high: {cpu_percent:.1f}%")
                status["healthy"] = False

            memory = psutil.virtual_memory()
            status["memory_percent"] = memory.percent
            status["memory_available_gb"] = memory.available / (1024**3)

            if memory.percent > 90:
                status["warnings"].append(
                    f"Memory usage critical: {memory.percent:.1f}% ({status['memory_available_gb']:.1f}GB available)"
                )
                status["healthy"] = False
            elif memory.percent > 80:
                status["warnings"].append(f"Memory usage high: {memory.percent:.1f}%")

            throttling = self._detect_cpu_throttling()
            if throttling:
                status["throttling_detected"] = True
                status["warnings"].append(
                    "CPU thermal throttling detected - performance may be degraded"
                )
                status["healthy"] = False

            try:
                disk = psutil.disk_usage("/")
                disk_free_gb = disk.free / (1024**3)
                if disk_free_gb < 1:
                    status["warnings"].append(
                        f"Disk space critically low: {disk_free_gb:.1f}GB free"
                    )
                    status["healthy"] = False
            except Exception:
                pass

            temp_warning = self._check_temperature()
            if temp_warning:
                status["temperature_warning"] = True
                status["warnings"].append("High system temperature detected")
                status["healthy"] = False

        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            status["warnings"].append(f"Monitoring error: {str(e)}")

        return status

    def _detect_cpu_throttling(self) -> bool:
        try:
            if not hasattr(psutil, "cpu_freq") or not self.initial_cpu_freq:
                return False

            current_freq = psutil.cpu_freq()
            if not current_freq:
                return False

            if current_freq.current < (self.initial_cpu_freq * 0.7):
                logger.warning(
                    f"Possible CPU throttling: {current_freq.current}MHz (started at {self.initial_cpu_freq}MHz)"
                )
                return True

        except Exception as e:
            logger.debug(f"Error detecting throttling: {e}")

        return False

    def _check_temperature(self) -> bool:
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        for entry in entries:
                            if entry.current > 85:
                                logger.warning(
                                    f"High temperature detected: {name} {entry.label} = {entry.current}°C"
                                )
                                return True
        except Exception as e:
            logger.debug(f"Temperature check not available: {e}")

        return False

    def get_safe_batch_size_recommendation(self) -> Optional[int]:
        try:
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)

            if available_gb < 2:
                return 1
            elif available_gb < 4:
                return 3
            elif available_gb < 8:
                return 5
            else:
                return None

        except Exception:
            return 5

    def log_system_info(self):
        try:
            cpu_count = psutil.cpu_count(logical=False)
            cpu_count_logical = psutil.cpu_count(logical=True)
            memory = psutil.virtual_memory()

            logger.info("=" * 60)
            logger.info("System Information")
            logger.info("=" * 60)
            logger.info(f"Platform: {platform.system()} {platform.release()}")
            logger.info(f"CPU: {cpu_count} cores ({cpu_count_logical} logical)")

            if hasattr(psutil, "cpu_freq"):
                freq = psutil.cpu_freq()
                if freq:
                    logger.info(
                        f"CPU Frequency: {freq.current:.0f}MHz (max: {freq.max:.0f}MHz)"
                    )

            logger.info(f"Total Memory: {memory.total / (1024**3):.1f}GB")
            logger.info(
                f"Available Memory: {memory.available / (1024**3):.1f}GB ({memory.percent:.1f}% used)"
            )
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Error logging system info: {e}")


def create_monitoring_report() -> str:
    monitor = HardwareMonitor()
    status = monitor.check_system_health()

    report = ["System Health Report", "=" * 40]
    report.append(
        f"Status: {'✅ Healthy' if status['healthy'] else '⚠️ Issues Detected'}"
    )
    report.append(f"CPU Usage: {status['cpu_percent']:.1f}%")
    report.append(
        f"Memory Usage: {status['memory_percent']:.1f}% ({status['memory_available_gb']:.1f}GB available)"
    )

    if status["throttling_detected"]:
        report.append("⚠️ CPU Throttling: DETECTED")

    if status["temperature_warning"]:
        report.append("⚠️ Temperature: HIGH")

    if status["warnings"]:
        report.append("\nWarnings:")
        for warning in status["warnings"]:
            report.append(f"  • {warning}")

    return "\n".join(report)
