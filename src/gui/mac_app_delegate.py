import logging
import sys

from PySide6.QtCore import QTimer

logger = logging.getLogger(__name__)

try:  # PyObjC is only available on macOS
    import objc  # type: ignore
    from AppKit import NSApplication  # type: ignore
    from Foundation import NSObject  # type: ignore
except Exception:  # pragma: no cover - PyObjC missing on non-macOS environments
    objc = None  # type: ignore
    NSObject = object  # type: ignore
    NSApplication = None  # type: ignore


def _schedule_on_main_thread(callback):
    QTimer.singleShot(0, callback)


if sys.platform == "darwin" and objc is not None:

    class _MacAppDelegate(NSObject):  # pragma: no cover - requires macOS runtime
        def initWithMainWindow_(self, window):  # noqa: N802 (PyObjC naming)
            self = objc.super(_MacAppDelegate, self).init()  # type: ignore[attr-defined]
            if self is None:
                return None
            self._window = window
            return self

        def application_openFiles_(self, application, filenames):  # noqa: N802
            import os

            if not filenames:
                self._activate_window()
                return

            # Finder can pass bootstrap/runtime artifacts; focus on actual files
            file_list = []
            for path in filenames:
                path_str = str(path)
                if (
                    "resource_tracker" in path_str
                    or "import " in path_str
                    or not os.path.exists(path_str)
                    or path_str.endswith(".py")
                ):
                    logger.debug("Ignoring non-input path: %s", path_str)
                    continue
                file_list.append(path_str)

            if not file_list:
                self._activate_window()
                return

            def deliver():
                if hasattr(self._window, "handle_external_file_open"):
                    self._window.handle_external_file_open(file_list)

            _schedule_on_main_thread(deliver)

        def applicationShouldHandleReopen_hasVisibleWindows_(self, application, flag):  # noqa: N802
            self._activate_window()
            return True

        def _activate_window(self):
            def activate():
                if hasattr(self._window, "bring_window_to_front"):
                    self._window.bring_window_to_front()

            _schedule_on_main_thread(activate)


else:
    _MacAppDelegate = None  # type: ignore


def register_mac_delegate(window):
    if sys.platform != "darwin":
        return None

    if _MacAppDelegate is None or NSApplication is None:
        logger.info("PyObjC not available - macOS delegate disabled")
        return None

    ns_app = NSApplication.sharedApplication()
    delegate = _MacAppDelegate.alloc().initWithMainWindow_(window)
    ns_app.setDelegate_(delegate)
    logger.info("macOS NSApplicationDelegate registered for open-file events")
    return delegate
