# Transcriber & Translator Tool Documentation

**Document Date:** April 30, 2025 (Review annually or when dependencies break)

## Table of Contents

- [Quick Start (copy/paste)](#quick-start-copypaste)
- [API Key Setup](#api-key-setup)
  - [OpenAI API Key](#openai-api-key)
  - [Google Cloud Translation Key](#google-cloud-translation-key)
- [Installation & Dependencies](#installation--dependencies)
  - [System Tools (ffmpeg)](#system-tools-ffmpeg)
  - [Python Environment & Packages](#python-environment--packages)
- [Directory Layout & File Locations](#directory-layout--file-locations)
- [Usage Examples](#usage-examples)
- [How It Works](#how-it-works)
  - [File-type Processing](#file-type-processing)
  - [Transcription (API vs Local)](#transcription-api-vs-local)
  - [Translation](#translation)
- [Pricing Estimate](#pricing-estimate)
- [Future Maintenance Notes](#future-maintenance-notes)

---

# Quick Start (copy/paste)

Follow these steps in your terminal.

**1. Set API Environment Variables (Choose your OS)**

   * **macOS (using zsh/bash):**
       * *Add to `~/.zshenv` (for zsh) or `~/.bash_profile` / `~/.bashrc` (for bash):*
           ```bash
           echo 'export OPENAI_API_KEY="sk-..."' >> ~/.zshenv
           echo 'export GOOGLE_APPLICATION_CREDENTIALS="$HOME/path/to/your_credentials.json"' >> ~/.zshenv
           ```
       * *Apply immediately in your current terminal:*
           ```bash
           source ~/.zshenv # Or your relevant bash profile file
           ```

   * **Windows (using Command Prompt - `cmd.exe`):**
       * *Run these commands. Replace paths/keys as needed.*
           ```batch
           setx OPENAI_API_KEY "sk-..."
           setx GOOGLE_APPLICATION_CREDENTIALS "%USERPROFILE%\path\to\your_credentials.json"
           ```
       * **IMPORTANT:** Close your current Command Prompt window and open a new one for these settings to take effect. `setx` does not affect the current window.

**2. Install System Tools (`ffmpeg`)**

   * **macOS:**
       ```bash
       brew install ffmpeg
       ```
   * **Windows (using Chocolatey):**
       ```powershell
       choco install ffmpeg -y
       ```
       *(You might need to run this in an Administrator PowerShell/Command Prompt)*

**3. Create & Activate Python Virtual Environment**

   * **macOS:**
       ```bash
       python3 -m venv env
       source env/bin/activate
       ```
   * **Windows (Command Prompt):**
       ```batch
       python -m venv env
       env\Scripts\activate.bat
       ```

**4. Install Python Dependencies**

   * *(Run this after activating your virtual environment)*
       ```bash
       pip install openai yt-dlp google-cloud-translate whisper python-dotenv requests
       ```
       *(Note: Installing Whisper directly from git is often recommended for latest updates)*


**5. Verify Setup & Run**

   ```bash
   # Check available options
   python trans.py --help

   # Example: Transcribe a local file using the API
   # python trans.py --file your_video.mp4
````

-----

# API Key Setup

This tool requires API keys for OpenAI (for transcription via API) and Google Cloud (for translation). Set these as environment variables so the script can access them securely.

## OpenAI API Key

1.  Obtain your API key from your [OpenAI Account Settings](https://platform.openai.com/account/api-keys).

2.  Set it as an environment variable named `OPENAI_API_KEY`.

      * **macOS (Temporary for session):**

        ```bash
        export OPENAI_API_KEY="sk-..."
        ```

        *(For persistence, add this line to `~/.zshenv` or `~/.bash_profile` as shown in Quick Start)*

      * **Windows (Command Prompt - Permanent):**

        ```batch
        setx OPENAI_API_KEY "sk-..."
        ```

        *(Remember to open a new terminal after running `setx`)*

3.  The Python script (`trans.py`) should include code to load this:

    ```python
    import os
    from dotenv import load_dotenv

    load_dotenv() # Optionally load from a .env file first
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise EnvironmentError("Error: OPENAI_API_KEY environment variable not set.")
    ```

## Google Cloud Translation Key

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).

2.  Create a new GCP project (or select an existing one).

3.  Enable the **Cloud Translation API** for your project.

4.  Go to **APIs & Services \> Credentials**.

5.  Click **Create Credentials \> Service account key**.

6.  Follow the prompts to create a service account (or use an existing one), select **JSON** as the key type, and download the key file.

7.  Save the JSON file to a secure location (e.g., inside your user directory but **outside** your project's code repository).

8.  Set the *full path* to this JSON file as an environment variable named `GOOGLE_APPLICATION_CREDENTIALS`.

      * **macOS (Temporary for session):**

        ```bash
        export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/downloaded-key-file.json"
        # Example: export GOOGLE_APPLICATION_CREDENTIALS="$HOME/gcp_keys/my-project-key.json"
        ```

        *(For persistence, add this line to `~/.zshenv` or `~/.bash_profile` as shown in Quick Start)*

      * **Windows (Command Prompt - Permanent):**

        ```batch
        setx GOOGLE_APPLICATION_CREDENTIALS "C:\path\to\your\downloaded-key-file.json"
        # Example: setx GOOGLE_APPLICATION_CREDENTIALS "%USERPROFILE%\gcp_keys\my-project-key.json"
        ```

        *(Use the actual full path. Remember to open a new terminal after running `setx`)*

-----

# Installation & Dependencies

*(Covered in [Quick Start](https://www.google.com/search?q=%23quick-start-copypaste). Refer back for commands.)*

## System Tools (ffmpeg)

FFmpeg is required for extracting audio from video files. Install it using your system's package manager:

  * **macOS:** `brew install ffmpeg`
  * **Windows:** `choco install ffmpeg -y` (using Chocolatey)

## Python Environment & Packages

It's highly recommended to use a Python virtual environment (`venv`) to manage dependencies.

1.  **Create venv:** `python -m venv env`
2.  **Activate venv:**
      * macOS/Linux: `source env/bin/activate`
      * Windows (cmd): `env\Scripts\activate.bat`
3.  **Install Packages:** Use the `pip install ...` command from the [Quick Start](https://www.google.com/search?q=%23quick-start-copypaste) section. The required packages are:
      * `openai`: Official OpenAI SDK (for API calls).
      * `yt-dlp`: Downloads audio/video (YouTube, etc.).
      * `google-cloud-translate`: Google Translation API client.
      * `openai-whisper`: Local transcription model (installed from git).
      * `python-dotenv`: Loads environment variables from a `.env` file (optional).
      * `requests`: HTTP library (often a dependency, good to include explicitly).

-----

# Directory Layout & File Locations

```text
.
├── audio_files/          # Downloaded/extracted MP3 audio files
├── transcripts/          # Generated VTT subtitle files (original & translated)
├── env/                    # Python virtual environment directory
├── trans.py                # The main command-line interface script
└── your_credentials.json   # Example location for GCP key (Keep secure!)
└── .env                    # Optional file for environment variables (add to .gitignore!)
```

  - **`audio_files/`**: Stores `.mp3` files extracted from videos or downloaded directly. Created automatically if it doesn't exist.
  - **`transcripts/`**: Stores output `.vtt` files. Created automatically.
      - Original language: `original_<basename>_<lang>.vtt`
      - Translated (English): `<basename>_<timestamp>_en.vtt`

-----

# Usage Examples

*(Ensure your virtual environment is activated before running)*

```bash
# Transcribe a local MP4 file using the OpenAI API
# Output: transcripts/original_video_xx.vtt (xx = detected language)
python trans.py --file video.mp4

# Transcribe MP4 locally using Whisper model AND translate to English
# Outputs: transcripts/original_video_xx.vtt
#          transcripts/video_YYYYMMDDHHMMSS_en.vtt
python trans.py --file video.mp4 --local --translate

# Download audio from a YouTube video, transcribe via API, and translate
# Ensure the URL is quoted if it contains special characters
# Outputs: transcripts/original_youtubevid_xx.vtt
#          transcripts/youtubevid_YYYYMMDDHHMMSS_en.vtt
python trans.py --youtube "[https://youtu.be/xyz](https://youtu.be/xyz)" --translate
# Note: Replace the example URL with a real one.

# Translate an existing English VTT subtitle file to a target language (e.g., Nepali 'ne')
# Requires modifications to the script logic to support target languages other than English.
# Current script translates *to* English. Assuming modification for this example:
# Input: captions_en.vtt
# Output: transcripts/captions_en_YYYYMMDDHHMMSS_ne.vtt
# python trans.py --file captions_en.vtt --vtt --target-lang ne

# Translate an existing non-English VTT file TO English
# Input: captions_es.vtt (Spanish)
# Output: transcripts/captions_es_YYYYMMDDHHMMSS_en.vtt
python trans.py --file captions_es.vtt --vtt --translate
```

-----

# How It Works

## File-type Processing

The script determines the input type and processes accordingly:

1.  **Video (`.mp4`, `.mov`, etc.)**: Uses `ffmpeg` to extract the audio stream into an `.mp3` file saved in `audio_files/`.
2.  **YouTube URL**: Uses `yt-dlp` to download the best available audio format and converts it to `.mp3`, saving it in `audio_files/`.
3.  **Audio (`.mp3`, etc.)**: Uses the audio file directly for transcription.
4.  **VTT Subtitle (`.vtt`)**: Parses the VTT file. If `--translate` is used, passes the text content to the translation step. Skips transcription.

## Transcription (API vs Local)

Produces a `.vtt` subtitle file from the audio.

  * **API (Default)**:
      * Uploads the `.mp3` file to the OpenAI Whisper API endpoint.
      * Receives transcription results, potentially including language detection.
      * Formats the output as `original_<basename>_<lang>.vtt` in the `transcripts/` directory.
  * **Local (`--local` flag)**:
      * Loads the `openai-whisper` model into memory (can be CPU or GPU intensive).
      * Processes the `.mp3` file locally.
      * Formats the output as `original_<basename>_<lang>.vtt`.

## Translation (`--translate` flag)

Translates the text content (from transcription or an input VTT file) into English.

1.  Parses the original `.vtt` file to extract text segments.
2.  Sends text segments to the Google Cloud Translation API.
3.  Receives English translations.
4.  Formats the translated text back into a new `.vtt` file, saved as `<basename>_<timestamp>_en.vtt` in the `transcripts/` directory.

-----

# Pricing Estimate

*Pricing is subject to change. Check provider websites for current rates.*

  * **OpenAI Whisper API**: Approximately **$0.006 per minute** of audio processed.
      * Example: A 60-minute audio file costs roughly $0.36.
  * **Google Cloud Translation API**:
      * **Free Tier**: Up to 500,000 characters per month.
      * **Standard Pricing**: Approximately **$20 per 1 million characters** after the free tier.
  * **Local Whisper**: No direct cost, but requires computational resources (CPU/GPU time, electricity). Larger models require more RAM/VRAM.

-----

# Future Maintenance Notes

  * **Check for Outdated Packages:** Periodically run `pip list --outdated` within the activated virtual environment. Upgrade packages using `pip install --upgrade <package_name>`. Be mindful of potential breaking changes in major version upgrades.
  * **Update System Tools:** Keep `ffmpeg` updated via `brew upgrade ffmpeg` (macOS) or `choco upgrade ffmpeg` (Windows).
  * **API Changes:** Monitor OpenAI and Google Cloud documentation/blogs for announcements about API changes or deprecations that might affect the script.
  * **Whisper Model Updates:** If using the git installation method for Whisper, you can update it by running the `pip install --upgrade git+...` command again.
  * **Review this Document:** Check annually or if dependencies cause issues. Update commands, links, and pricing estimates as needed.

<!-- end list -->
