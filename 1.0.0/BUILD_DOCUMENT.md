# Build & Verification Guide (macOS)

This document describes **how xScribe is actually built and run today**.

It is provided for:

* Source verification & auditing
* Development and personal modification
* Reproducing local builds

> Note: This repository is **source-first**. While a signed macOS app has been produced using `py2app`, packaged binaries are not the primary distribution mechanism in this repo.

---

## Platform Requirements

* macOS (Apple Silicon or Intel)
* Python **3.11.x**
* Xcode Command Line Tools

Install Xcode CLI tools:

```bash
xcode-select --install
```

---

## System Dependencies

### FFmpeg (Required)

xScribe relies on `ffmpeg` for audio/video processing. The project **does not bundle ffmpeg** in the repository.

Install via Homebrew:

```bash
brew install ffmpeg
```

Ensure it is available on PATH:

```bash
ffmpeg -version
```

---

## Python Environment Setup

Create and activate a virtual environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Running xScribe from Source

xScribe can be run directly from source during development.

Typical entry point:

```bash
python xscribe.py
```

(Adjust this command if your local entry point differs.)

---

## Testing

xScribe includes unit, functionality, and integration tests.

### Run unit + functionality tests

```bash
pytest -m "not integration"
```

### Run integration tests (requires ffmpeg, Whisper, and test fixtures)

```bash
pytest -m integration
```

Integration tests exercise the full transcription pipeline on real media files.

---

## macOS App Packaging (py2app)

> **Used and verified**

xScribe has been successfully built and signed as a macOS application using **py2app**.

This workflow is intended for:

* Local distribution
* Personal builds
* Verification that the application can be packaged

### High-level process

1. Ensure dependencies are installed
2. Configure `setup.py` or py2app configuration
3. Build the app bundle

```bash
python setup.py py2app
```

4. (Optional) Sign the resulting `.app`

```bash
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: YOUR NAME" dist/xScribe.app
```

> py2app configuration may change over time and is considered **maintenance-heavy**.
> The source-based workflow is the primary supported path in this repository.

---

## Project Structure (Overview)

```text
src/                    # Application source
  core/                 # Transcription & processing logic
  gui/                  # GUI components & workers
  models/               # Data models
  services/             # Higher-level orchestration

tests/                  # Tests
  tests/                # accuracy / functionality / integration
  fixtures/             # Media & transcript fixtures

assets/                 # Icons and assets
requirements.txt        # Python dependencies
pytest.ini              # Pytest configuration
README.md               # Project overview
```

---

## Privacy & Network Behavior

* Transcription is fully local
* No cloud APIs are used
* Network access is limited to **initial model downloads** (e.g. Whisper model weights)

One purpose of providing source builds is to allow independent verification of these claims.

---

## Troubleshooting

**ffmpeg not found**

```text
RuntimeError: ffmpeg is not installed or not on PATH
```

Install via Homebrew and restart your shell.

**Whisper warnings about fp16**

* Automatically handled by disabling fp16 when running on CPU

---

## Licensing & Support

* This repository is provided for inspection, learning, and modification
* Official support (if any) applies only to distributed binaries, not custom source builds

---

✅ This document intentionally reflects **what is actually used**, not hypothetical tooling.
