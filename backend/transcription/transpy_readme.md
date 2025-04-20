## Table of Contents

- [Quick Start (copy/paste)](#quick-start-copypaste)
- [API Key Setup](#api-key-setup)
- [Installation \& Dependencies](#installation--dependencies)
  - [System Tools (ffmpeg)](#system-tools-ffmpeg)
  - [Python Packages](#python-packages)
- [Directory Layout \& File Locations](#directory-layout--file-locations)
- [Usage Examples](#usage-examples)
- [How It Works](#how-it-works)
  - [File-type Processing](#file-type-processing)
  - [Transcription (API vs Local)](#transcription-api-vs-local)
  - [Translation](#translation)
- [Pricing Estimate](#pricing-estimate)
- [Future Maintenance Notes](#future-maintenance-notes)

---

# Quick Start (copy/paste)

```bash
# 1. Set environment variables
#    macOS (zsh): ~/.zshenv or ~/.zprofile
echo 'export OPENAI_API_KEY="sk-…"' >> ~/.zshenv
echo 'export GOOGLE_APPLICATION_CREDENTIALS="$HOME/path/to/credentials.json"' >> ~/.zshenv
source ~/.zshenv

# 2. Install system tools
brew install ffmpeg    # macOS
choco install ffmpeg -y  # Windows

# 3. Create & activate Python venv
python3 -m venv env && source env/bin/activate

# 4. Install Python dependencies
pip install openai                  # OpenAI SDK
pip install yt-dlp                  # yt-dlp downloader
pip install --upgrade google-cloud-translate  # Google Translate client
pip install openai-whisper          # Local Whisper model

# 5. Run help to see usage
./transcribe.py --help
```

---

# API Key Setup

- **OpenAI**:\
  Store your API key as an environment variable:

  ```bash
  export OPENAI_API_KEY="sk-…"
  ```

  In Python:

  ```python
  OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
  if not OPENAI_API_KEY:
      raise RuntimeError("Please set OPENAI_API_KEY")
  ```

- **Google Cloud Translate**:

  1. Create a GCP project and enable the **Cloud Translation API**.
  2. Generate a JSON key under **APIs & Services > Credentials**.
  3. Export its path:
     ```bash
     export GOOGLE_APPLICATION_CREDENTIALS="$HOME/credentials.json"
     ```

---

# Installation & Dependencies

## System Tools (ffmpeg)

- **macOS**:
  ```bash
  brew install ffmpeg
  ```
- **Windows**:
  ```powershell
  choco install ffmpeg -y
  ```

## Python Packages

| Package                   | Install Command                                       | Description                                           |
|---------------------------|-------------------------------------------------------|-------------------------------------------------------|
| `requests`                | `pip install requests`                                | HTTP library for API calls and downloads              |
| `yt-dlp`                  | `pip install yt-dlp`                                  | Audio/video downloader (YouTube et al.)               |
| `google-cloud-translate`  | `pip install --upgrade google-cloud-translate`       | Google Cloud Translation client library               |
| `openai-whisper`          | `pip install openai-whisper`                         | Local Whisper speech-to-text model                    |
| `openai` _(optional)_     | `pip install openai`                                  | Official OpenAI Python SDK (if you prefer SDK calls) |

---------------------------|-------------------------------------------------------|-------------------------------------|
| `requests`                | `pip install requests`                                | HTTP library for API calls and downloads |
| `openai`                  | `pip install openai`                                 | Official OpenAI Python SDK          |
| `yt-dlp`                  | `pip install yt-dlp`                                 | Audio/video downloader              |
| `google-cloud-translate`  | `pip install --upgrade google-cloud-translate`       | Google Translate client library     |
| `openai-whisper`          | `pip install openai-whisper`                         | Local Whisper speech-to-text model  |

------------------------ | ---------------------------------------------- | ---------------------------------- |
| `openai`                 | `pip install openai`                           | Official OpenAI Python SDK         |
| `yt-dlp`                 | `pip install yt-dlp`                           | Audio/video downloader             |
| `google-cloud-translate` | `pip install --upgrade google-cloud-translate` | Google Translate client library    |
| `openai-whisper`         | `pip install openai-whisper`                   | Local Whisper speech‑to‑text model |

---

# Directory Layout & File Locations

```text
.
├── audio_files/      # downloaded or extracted .mp3 files
├── transcripts/      # generated .vtt files (original and translated)
├── transcribe.py     # main CLI script
└── env/              # Python virtual environment
```

- **audio\_files/**: MP3s from video extractions or YouTube downloads.
- **transcripts/**: Contains `original_<basename>_<lang>.vtt` and translated `<basename>_<timestamp>_en.vtt`.

---

# Usage Examples

```bash
# Transcribe a single MP4 via API
./transcribe.py --file video.mp4

# Transcribe locally (Whisper) and translate
./transcribe.py --file video.mp4 --local --translate

# Download & transcribe YouTube audio
./transcribe.py --youtube https://youtu.be/xyz --translate

# Translate an existing VTT subtitles file
./transcribe.py --file captions.vtt --vtt
```

---

# How It Works

## File-type Processing

- **Video (MP4/MOV)** → `ffmpeg` extracts to `basename.mp3`.
- **YouTube URL** → `yt-dlp` downloads best audio and converts to MP3.
- **MP3 input** → used directly.
- **VTT input** → parsed and optionally passed to translation.

## Transcription (API vs Local)

- **API (default)**: Calls OpenAI’s Whisper endpoint; outputs verbose segments in VTT.
- **Local**: Uses `openai-whisper` model in‑process (CPU/GPU).
- **Filename flow**: Generates `original_<basename>.vtt` then renames to include detected language code (e.g. `_en`).

## Translation

- Uses Google Cloud Translate to convert segment texts to English.
- Saves as `<basename>_<timestamp>_en.vtt`.
- **Free tier**: Up to 500 000 characters/month free.\*

---

# Pricing Estimate

- **Whisper API**: \$0.006 per minute of audio (\~\$0.36/hour).\*
- **Google Translate**: First 500 000 characters free; \$20 per million characters thereafter.

\*Subject to change per provider’s pricing updates.

---

# Future Maintenance Notes

- **Library updates**: Run `pip list --outdated`; upgrade via `pip install --upgrade <package>`.
- **API changes**: Monitor OpenAI and GCP changelogs for endpoint updates.
- **System tools**: Update FFmpeg via `brew upgrade ffmpeg` or `choco upgrade ffmpeg`.
- **Document date**: Created April 19, 2025; review annually or when dependencies break.

