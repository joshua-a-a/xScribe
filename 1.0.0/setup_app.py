"""
xScribe - py2app Setup Configuration for Standalone Distribution
"""

import os
import sys

from setuptools import setup

sys.setrecursionlimit(10000)

APP = ["xscribe.py"]

# Check ffmpeg exists
ffmpeg_source = "bin/ffmpeg"
if not os.path.exists(ffmpeg_source):
    print("⚠️  ERROR: bin/ffmpeg not found!")
    print("Run: chmod +x bundle_ffmpeg_unsigned.sh && ./bundle_ffmpeg_unsigned.sh")
    sys.exit(1)

DATA_FILES = [
    ("bin", ["bin/ffmpeg"]),
]

OPTIONS = {
    "alias": False,
    "argv_emulation": False,
    "iconfile": "assets/icon.icns",
    "site_packages": True,
    "compressed": False,
    "semi_standalone": False,
    "plist": {
        "CFBundleName": "xScribe",
        "CFBundleDisplayName": "xScribe",
        "CFBundleGetInfoString": "Audio & Video Transcription",
        "CFBundleIdentifier": "com.MacMasters.xScribe",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "NSHumanReadableCopyright": "© 2025 MacMasters. All rights reserved.",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "10.15.0",
        "NSMicrophoneUsageDescription": "xScribe needs microphone access for transcription.",
        "LSMultipleInstancesProhibited": True,
        "CFBundleDocumentTypes": [
            {
                "CFBundleTypeName": "Audio Files",
                "CFBundleTypeRole": "Viewer",
                "LSItemContentTypes": ["public.mp3", "public.wav", "public.audio"],
                "LSHandlerRank": "Alternate",
            },
            {
                "CFBundleTypeName": "Video Files",
                "CFBundleTypeRole": "Viewer",
                "LSItemContentTypes": ["public.movie", "public.video"],
                "LSHandlerRank": "Alternate",
            },
        ],
        "PyExecutableName": "xScribe-bin",
        "PyResourcePackages": [
            "lib/python311.zip",
            "lib/python3.11",
        ],
    },
    "packages": [
        "src",
        "soundfile",
        "objc",
        "Foundation",
        "AppKit",
    ],
    "includes": [
        "whisper",
        "torch",
        "torchaudio",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "numpy",
        "librosa",
        "soundfile",
        "soundfile._soundfile_data",
        "scipy",
        "tiktoken",
        "more_itertools",
        "numba",
        "llvmlite",
        "certifi",
    ],
    "excludes": [
        # Exclude jaraco packages
        "jaraco",
        "jaraco.text",
        "jaraco.functools",
        "jaraco.context",
        "jaraco.collections",
        "jaraco.classes",
        # Exclude PIL/Pillow (not needed for audio transcription, causes signing issues)
        "PIL",
        "Pillow",
        # Other standard excludes
        "setuptools",
        "setuptools._vendor",
        "backports",
        "backports.tarfile",
        "PyInstaller",
        "tkinter",
        "matplotlib",
        "IPython",
        "jupyter",
        "pytest",
        "sphinx",
        "test",
        "tests",
    ],
    "strip": False,
    "optimize": 0,
}

setup(
    name="xScribe",
    version="1.0.0",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
)

# Post-build verification
if "py2app" in sys.argv:
    import time

    time.sleep(2)

    app_path = "dist/xScribe.app"
    if os.path.exists(app_path):
        print("\n" + "=" * 60)
        print("POST-BUILD VERIFICATION")
        print("=" * 60)

        python_dir = f"{app_path}/Contents/Resources/lib/python3.11"

        print("\nChecking core packages:")
        for pkg in ["whisper", "torch", "PySide6", "numpy", "src"]:
            pkg_path = f"{python_dir}/{pkg}"
            if os.path.exists(pkg_path):
                print(f"   {pkg}")
            else:
                print(f"   {pkg} MISSING")

        # Verify jaraco was NOT included
        jaraco_path = f"{python_dir}/jaraco"

        if not os.path.exists(jaraco_path):
            print("   jaraco correctly excluded")
        else:
            print("   jaraco was included (will cause issues)")

        # Check the bootstrap file
        boot_file = f"{app_path}/Contents/Resources/__boot__.py"
        if os.path.exists(boot_file):
            with open(boot_file, "r") as f:
                boot_content = f.read()
                if "pkg_resources" in boot_content:
                    print("   __boot__.py imports pkg_resources (needs patching)")
                else:
                    print("   __boot__.py does not import pkg_resources")

        print("\n" + "=" * 60)
        print("BUILD COMPLETE")
        print("=" * 60)
        print("\nTest with: open dist/xScribe.app")
