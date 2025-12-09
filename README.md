# xScribe-1.0.0

**Private & Local Transcription - Powered by AI, No Cloud, No Compromises**

xScribe is a privacy focused audio and video transcription application for Mac. Powered by OpenAI's Whisper models, it processes everything locally on your device. Your audio never leaves your computer.

---

## Why xScribe?

**For professionals who can't compromise on privacy:**

- **Personal** - Transcribe diaries, voice notes, and personal audio securely
- **Legal** - Consultant-client privilege intact by processing on your Mac only
- **Medical** - Healthcare compliance matched by local processing  
- **Publishing** - No risk leaking unpublished manuscripts and interviews
- **Enterprise** - Meet corporate data security requirements

**No subscriptions. No cloud. No compromises.**

---

## Features

### Core Transcription
- **Multiple AI Models** - Choose from Tiny, Base, Small, or Medium for speed vs accuracy vs resource use
- **15-70x Real-Time** - A 1-hour recording transcribes in 1-4 minutes
- **99%+ Accuracy** - State of the art quality transcription on noisy and clean audio
- **Auto Language Detection** - Supports 10+ languages automatically

### Audio and Video Support
- **Audio Formats** - WAV, MP3, FLAC, M4A, OGG, OPUS, WEBM
- **Video Formats** - MP4, MOV, AVI, MKV, WebM, and 16 more
- **Automatic Extraction** - Drop a video file, get a transcript

### Professional Features
- **Speaker Detection** - Identify who said what in multi-person recordings
- **Batch Processing** - Queue dozens of files, process overnight
- **Audio Quality Analysis** - Get feedback on recording quality
- **Multiple Export Formats** - TXT, SRT subtitles, DOCX, JSON

### Privacy and Security
- **100% Offline** - Works without internet after initial model download
- **Zero Data Collection** - No telemetry, no analytics, no tracking
- **Local AI Models** - Downloaded once, stored on your Mac
- **Your Data Stays Yours** - Nothing ever leaves your device

---

## System Requirements

| Component     | Minimum                | Recommended            |
|---------------|------------------------|------------------------|
| **macOS**     | 15.0 Sequoia           | 26.0+ (Tahoe)          |
| **Processor** | 2018 excl. MacBook Air | Apple Silicon          |
| **RAM**       | 8 GB                   | 16 GB+                 |
| **Storage**   | 5 GB free              | 10 GB free             |

### Model Memory Requirements

| Model      | Download Size | RAM During Use | Best For              |
|------------|---------------|----------------|-----------------------|
| **Tiny**   | 75 MB         | ~1.5 GB        | Quick drafts, testing |
| **Base**   | 150 MB        | ~2 GB          | Daily transcription   |
| **Small**  | 500 MB        | ~3 GB          | Professional quality  |
| **Medium** | 1.5 GB        | ~5 GB          | Maximum accuracy      |

---

## Installation

1. **Download** the xScribe DMG from your purchase correspondence
2. **Double-click to Open** the DMG and drag xScribe to Applications
3. **Launch** xScribe from the Applications folder
4. **First Run** - Choose a model to download (All recommended - Base/Small if very little storage space available)
5. **Start Transcribing** - Drop files or click Browse, Batch processing supported too! 

> **Note:** The first launch downloads your chosen AI model (75 MB - 1.5 GB). After that, xScribe works completely offline unless you download the remaining models.

---

## Quick Start

### Single File
1. Click **Browse Files** or drag a file onto xScribe
2. Select your model (Base for most use cases)
3. Click **Transcribe**
4. Copy text or export to your preferred format

### Batch Processing
1. Click **Batch Mode**
2. Add multiple files (mix audio and video freely)
3. Select your model (Base for most use cases)
4. Click **Start Batch**
5. Export all results to a folder

### Speaker Detection
1. Enable **Speaker Detection/Diarization** before transcribing
2. xScribe identifies different voices automatically
3. Results show "Speaker 1:", "Speaker 2:", etc.

### Preprocessing for Noisy Audio
1. Enable **Audio Enhancement** in Settings
2. xScribe cleans background noise and improves clarity
3. Transcriptions are more accurate on difficult recordings - works with any model


---

## Choosing a Model

**Start with Base** - It handles 90% of use cases perfectly.

### Quick Decision Guide

| Model      | Speed         | Use When...                                  |
|------------|---------------|----------------------------------------------|
| **Tiny**   | 70x real-time | Testing, previewing, very clear audio        |
| **Base**   | 35x real-time | Podcasts, meetings, interviews, most content |
| **Small**  | 20x real-time | Important transcripts, multiple speakers     |
| **Medium** | 10x real-time | Heavy accents, technical jargon, noisy audio |

### When to Use Each Model

- **Just testing a file quickly or very high quality audio** - Tiny
- **Clear audio, one to two speakers** - Base
- **Multiple speakers, meetings to minutes, most video conferences** - Small  
- **Difficult/compressed/noisy/low quality audio, accents, background noise, webinars, complex content, technical jargon** - Medium


> **Tip:** Better recording quality helps more than a larger model. Base with clean audio beats Medium with noisy audio.

---

## Supported Formats

### Audio
`.wav` `.mp3` `.flac` `.m4a` `.ogg` `.opus` `.webm`

### Video  
`.mp4` `.m4v` `.mov` `.avi` `.mkv` `.webm` `.flv` `.wmv` `.mpg` `.mpeg` `.3gp` `.ogv` `.vob` `.mts` `.m2ts` `.ts` `.divx` `.xvid` `.asf` `.rm` `.rmvb`

### File Limits
- **Minimum size:** 1 KB
- **Maximum size:** 10 GB
- **Maximum duration:** 4 hours

> Files over 30 minutes show a confirmation with estimated processing time.

---

## Privacy

xScribe is built for privacy from the ground up:

- **No internet required** after initial model download  
- **No accounts** - no sign-up, no login  
- **No telemetry** - we don't track anything  
- **No cloud processing** - everything runs on your Mac  
- **No data collection** - your files are never accessed by anyone but you  

### Technical Privacy Features
- All AI processing uses local Whisper models
- Temporary files are securely deleted after processing
- No network connections during transcription
- Complete audit logging available for compliance verification

---

## Troubleshooting

### "Model not found" on first transcription
Select a different model from Settings, or click the model dropdown to trigger download.

### Slow transcription
- Use Base instead of Medium for faster results
- Close other heavy applications
- Check your Mac isn't thermal throttling (fans at max) 
- Activity monitor > CPU tab / Memory tab will reveal if your computer is running at maximum capability which could result in slowness. Reduce model size or close other applications.

### Video won't process
xScribe requires FFmpeg for video support. While we package FFmpeg with the application for ARM64 (Apple Silicon) processors, we cannot guarantee all dependencies work correctly for x86/64 (Intel) Macs. If you experience issues, you may need to install dependencies manually via Homebrew:
```bash
brew install ffmpeg
```

### Out of memory
- Use a smaller model (Base instead of Medium)
- Close other applications
- Process files one at a time instead of batch

### App won't open (security warning)
Right-click xScribe, then select Open, then click "Open" in the dialog. This is only needed once.

xScribe is code signed and notarised with Apple. However, the latest release may occasionally have delays in code signing due to quick patches and fixes. If you encounter a security warning, the right-click method above will allow you to run the application safely.

---

## Export Formats

| Format            | .ext  | Best For                |
|-------------------|-------|-------------------------|
| **Plain Text**    | .txt  | Simple reading, copying |
| **Subtitles**     | .srt  | Video captioning        |
| **Word Document** | .docx | Editing, formatting     |
| **JSON**          | .json | Integration, processing |

---

## Performance Benchmarks

Tested on Apple Silicon Propcessors, average performance times below:

| Audio Length | Base Model | Small Model | Medium Model |
|--------------|------------|-------------|--------------|
| 5 minutes    | ~10 sec    | ~15 sec     | ~30 sec      |
| 30 minutes   | ~40 sec    | ~1 min      | ~1 min       |
| 1 hour       | ~1 min     | ~1 min      | ~2 min       |
| 2 hours      | ~2 min     | ~2 min      | ~3 min      |

*Performance varies by Mac model, audio complexity, and speaker detection settings.*

---

## Getting Help

**Email:** support@macmasters.tech

When reporting issues, please include:
- macOS version
- Mac model (e.g., "M3 MacBook Pro")
- Model being used (Base, Small, etc.)
- File type and approximate duration
- Description of the issue

---

## Licence

> xScribe is proprietary software sold as a perpetual licence. Once you purchase xScribe, it's yours to keep forever.
> Note: This repository is provided for transparency and inspection by license holders.  
> Cloning or modifying the code is permitted for personal/internal use only, as described in LICENSE.md.

**Copyright 2025 Joshua Poulter. All rights reserved.**

---

## Version History

### 1.0.0 (December 2025)
- Initial release
- Whisper model support (Tiny, Base, Small, Medium)
