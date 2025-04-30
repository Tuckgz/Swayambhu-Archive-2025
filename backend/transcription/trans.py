#!/usr/bin/env python3
import os
import sys
import glob
import argparse
import subprocess
import requests
from datetime import datetime
import yt_dlp as youtube_dl
from google.cloud import translate_v2 as translate
from dotenv import load_dotenv

load_dotenv()

# --- Google Translate Setup ---
# Option 1: Use environment variable (Recommended)
google_creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not google_creds_path:
    # Option 2: Hardcoded path (Fallback - less flexible, remove if using env var)
    google_creds_path = "/Users/tuckr/APIs/Google Cloud/swayambhu-451702-e759a9ee59ab.json"
    print("Warning: Using hardcoded Google Credentials path. Set GOOGLE_APPLICATION_CREDENTIALS env var.")

if google_creds_path:
    google_creds_path = os.path.expanduser(google_creds_path)
    if os.path.exists(google_creds_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_creds_path
        google_client = translate.Client()
        print(f"Using Google Credentials: {google_creds_path}")
    else:
        print(f"Error: Google Credentials file not found at {google_creds_path}")
        google_client = None # Or sys.exit("Exiting: Google Credentials not found.")
else:
    print("Error: GOOGLE_APPLICATION_CREDENTIALS environment variable not set and no fallback path provided.")
    google_client = None # Or sys.exit("Exiting: Google Credentials not configured.")


# --- OpenAI Setup ---
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    print("Warning: OPENAI_API_KEY environment variable not set. API transcription will fail.")
    # Consider adding sys.exit() here if API key is strictly required

# Ensure required directories exist
os.makedirs("audio_files", exist_ok=True)
os.makedirs("transcripts", exist_ok=True)

# ---------------------
# HELPER FUNCTIONS (Unchanged - keep as is)
# ---------------------
def get_timestamp():
    """Generate a unique timestamp string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def format_vtt_timestamp(seconds):
    """Convert seconds to VTT timestamp format (HH:MM:SS.mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}.{millisecs:03}"

def adjust_filepath(filepath):
    """Remove 'backend/' prefix if present."""
    # Consider if this is still needed or can be simplified/removed
    if filepath and filepath.startswith("backend/"):
        return filepath[len("backend/"):]
    return filepath

# ---------------------
# MEDIA PROCESSING FUNCTIONS (Unchanged - keep as is)
# ---------------------
def extract_audio_from_video(input_path):
    """Extract audio from a video file (MOV/MP4) and save as MP3."""
    base = os.path.splitext(os.path.basename(input_path))[0]
    output_audio_path = os.path.join("audio_files", f"{base}.mp3")
    # Check if MP3 already exists to avoid re-extraction
    if os.path.exists(output_audio_path):
        print(f"Audio file already exists: {output_audio_path}")
        return output_audio_path
    print(f"Extracting audio from {input_path} to {output_audio_path}...")
    command = [
        "ffmpeg", "-y", # Overwrite output without asking
        "-i", input_path,
        "-vn", # No video
        "-acodec", "mp3",
        "-ar", "44100", # Audio sample rate
        "-ac", "2", # Stereo audio channels
        "-ab", "192k", # Audio bitrate
        output_audio_path
    ]
    try:
        # Show ffmpeg output for debugging, remove DEVNULL to see errors/progress
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        print("Audio extraction successful.")
        return output_audio_path
    except subprocess.CalledProcessError as e:
        print(f"Error during ffmpeg execution: {e}")
        print(f"FFmpeg stderr: {e.stderr.decode()}")
        return None
    except FileNotFoundError:
        print("Error: ffmpeg not found. Make sure it's installed and in your PATH.")
        return None


def download_audio(youtube_url):
    """Download audio from a YouTube URL and convert it to MP3."""
    # Define a safer filename based on URL or video ID if possible
    # For simplicity, keeping a generic name, but could be improved
    output_tmpl = os.path.join("audio_files", "%(title)s_%(id)s.%(ext)s")
    mp3_output_path = "" # Will be determined after download

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_tmpl, # Template for filename
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192', # Corresponds to -ab 192k
        }],
        'noplaylist': True, # Prevent downloading entire playlists
        'quiet': False, # Show yt-dlp output
        'progress': True,
    }
    print(f"Attempting to download YouTube audio from: {youtube_url}")
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=True)
            # Construct the expected MP3 path based on the template and info_dict
            base_filename = ydl.prepare_filename(info_dict).rsplit('.', 1)[0]
            mp3_output_path = base_filename + ".mp3"

        if os.path.exists(mp3_output_path):
             print(f"Audio downloaded and saved as: {mp3_output_path}")
             return mp3_output_path
        else:
             # Sometimes yt-dlp might save with slightly different name, search for the mp3
             downloaded_files = glob.glob(os.path.join("audio_files", "*.mp3"))
             if downloaded_files:
                 # Assuming the latest mp3 in the folder is the one we just downloaded
                 latest_file = max(downloaded_files, key=os.path.getctime)
                 print(f"Audio likely saved as: {latest_file} (assuming latest)")
                 return latest_file
             else:
                 print("Error: MP3 file not found after download attempt.")
                 return None

    except Exception as e:
        print(f"Error during YouTube download or processing: {e}")
        return None


# ---------------------
# TRANSCRIPTION FUNCTIONS (Keep original transcribe_audio, no changes needed here)
# ---------------------
def transcribe_audio(audio_path, transcript_path, language_code=None, local=False):
    """
    Transcribe audio and generate a VTT file.
    When local is True, run local Whisper; otherwise, use the Whisper API.
    """
    if local:
        try:
            import whisper # Keep import here to make local optional
            print(f"Transcribing (local) {audio_path} ...")
            # Consider smaller models for faster testing e.g., "base", "small", "medium"
            model = whisper.load_model("large")
            # Use verbose=False for cleaner output unless debugging timestamps
            result = model.transcribe(audio_path, word_timestamps=True, verbose=False)
            detected_language = result.get("language", "unknown")
            print(f"Detected language: {detected_language}")

            segments = result["segments"]
            vtt_lines = ["WEBVTT", ""]
            for segment in segments:
                start_time = format_vtt_timestamp(segment["start"])
                end_time = format_vtt_timestamp(segment["end"])
                text = segment["text"].strip()
                vtt_lines.extend([f"{start_time} --> {end_time}", text, ""])

            # Write initial file before potential rename
            temp_transcript_path = transcript_path # Use the initially calculated path
            with open(temp_transcript_path, "w", encoding="utf-8") as f:
                f.write("\n".join(vtt_lines))
            print(f"Saved initial VTT transcription to {temp_transcript_path}")
            return segments, detected_language, temp_transcript_path # Return path for renaming

        except ImportError:
             print("Error: 'openai-whisper' package not installed. Cannot use --local.")
             print("Install it via: pip install -U openai-whisper")
             return None, None, None
        except Exception as e:
            print(f"Error during local transcription: {e}")
            return None, None, None

    else: # API Transcription
        if not openai_key:
            print("Error: OpenAI API key not set. Cannot use API transcription.")
            return None, None, None
        print(f"Transcribing via API {audio_path} ...")
        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {openai_key}"}
        data = {
            "model": "whisper-1",
            "response_format": "verbose_json", # Get segments and timestamps
            # "response_format": "vtt", # Alternative: Get VTT directly
            "timestamp_granularities": ["segment"] # Request segment-level timestamps
        }
        if language_code:
            data["language"] = language_code
            print(f"Using forced language for API: {language_code}")

        try:
            with open(audio_path, "rb") as audio_data:
                files = {"file": (os.path.basename(audio_path), audio_data)}
                response = requests.post(url, headers=headers, data=data, files=files)

            if response.status_code != 200:
                print(f"Error: API returned status {response.status_code}")
                print(f"Response: {response.text}")
                return None, None, None

            result = response.json()
            detected_language = result.get("language", "unknown")
            print(f"Detected language (API): {detected_language}")
            segments = result.get("segments", [])
            if not segments:
                print("Warning: No segments found in API response.")
                 # Check if 'text' exists for basic transcript
                full_text = result.get("text")
                if full_text:
                     print("API returned full text but no segments. Cannot create VTT.")
                     # Optionally save full text to a .txt file here
                return None, detected_language, None # Return lang even if no segments

            # --- Create VTT from verbose_json segments ---
            vtt_lines = ["WEBVTT", ""]
            for segment in segments:
                start_time = format_vtt_timestamp(segment["start"])
                end_time = format_vtt_timestamp(segment["end"])
                text = segment["text"].strip()
                vtt_lines.extend([f"{start_time} --> {end_time}", text, ""])

            # Write initial file before potential rename
            temp_transcript_path = transcript_path # Use the initially calculated path
            with open(temp_transcript_path, "w", encoding="utf-8") as f:
                f.write("\n".join(vtt_lines))
            print(f"Saved VTT transcription to {temp_transcript_path}")
            return segments, detected_language, temp_transcript_path # Return path

        except requests.exceptions.RequestException as e:
            print(f"Network error during API transcription: {e}")
            return None, None, None
        except Exception as e:
            print(f"Exception during API transcription processing: {e}")
            return None, None, None

# ---------------------
# TRANSLATION FUNCTIONS
# ---------------------
def translate_text_google(text_list, target_language="en"):
    """Translates a list of texts using Google Translate."""
    if not google_client:
        print("Error: Google Translate client not initialized. Cannot translate.")
        return None # Indicate failure
    if not text_list:
        return [] # Return empty list for empty input

    try:
        if isinstance(text_list, list):
            # Ensure all items are strings
            text_list = [str(item) for item in text_list]
            # Google Translate API handles batching internally
            result = google_client.translate(text_list, target_language=target_language)
            # Extract translated text, handle potential errors if needed
            return [res['translatedText'] for res in result]
        else: # Single string input
            result = google_client.translate(str(text_list), target_language=target_language)
            return result['translatedText']
    except Exception as e:
        print(f"Error during Google Translate API call: {e}")
        # Handle specific API errors if necessary (e.g., invalid language code)
        return None # Indicate failure


def translate_vtt(segments, target_lang, source_file_path):
    """Translate segments and write a VTT file."""
    if not segments:
        print("No segments provided for translation.")
        return

    print(f"Translating text to target language: {target_lang}...")
    texts = [seg["text"].strip() for seg in segments]

    translated_texts = translate_text_google(texts, target_language=target_lang)

    if translated_texts is None:
        print("Translation failed. Skipping VTT generation.")
        return # Stop if translation failed

    if len(translated_texts) != len(segments):
        print("Warning: Mismatch between number of original and translated segments.")
        # Decide how to handle this: skip, error out, or try to match?
        # For now, we'll proceed but this indicates a potential issue.

    # Use the source file path (could be original audio or VTT) for base name
    base_name = os.path.splitext(os.path.basename(source_file_path))[0]
    # Clean up potential 'original_' prefix if it came from a transcript
    if base_name.startswith("original_"):
         base_name = base_name[len("original_"):].rsplit('_', 1)[0] # Remove lang code too

    timestamp = get_timestamp()
    translated_vtt_path = os.path.join(
        "transcripts",
        f"{base_name}_{timestamp}_{target_lang}.vtt" # Filename reflects target lang
    )

    vtt_lines = ["WEBVTT", ""]
    for idx, seg in enumerate(segments):
         # Check if index exists in translated_texts
        if idx < len(translated_texts):
             # Use original timestamps, handle if they are already formatted strings (from VTT input)
            start_time = seg["start"] if isinstance(seg["start"], str) else format_vtt_timestamp(seg["start"])
            end_time = seg["end"] if isinstance(seg["end"], str) else format_vtt_timestamp(seg["end"])
            translated_text = translated_texts[idx]
            vtt_lines.extend([f"{start_time} --> {end_time}", translated_text, ""])
        else:
            print(f"Warning: Missing translation for segment index {idx}")


    try:
        with open(translated_vtt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(vtt_lines))
        print(f"Translated VTT saved to: {translated_vtt_path}")
    except IOError as e:
        print(f"Error writing translated VTT file: {e}")


# ---------------------
# SUBTITLE PARSING FUNCTIONS (Unchanged - keep as is)
# ---------------------
def parse_vtt(vtt_file_path):
    """Parse a VTT file and return segments as a list of dicts."""
    segments = []
    try:
        with open(vtt_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        header_skipped = False
        current_segment = None
        time_line = None

        for line in lines:
            line = line.strip()
            if not header_skipped:
                if line.startswith("WEBVTT"):
                    header_skipped = True
                continue # Skip header lines

            if "-->" in line:
                # Start of a new segment cue
                if current_segment and time_line: # Save previous segment if exists
                     segments.append({"start": time_line[0], "end": time_line[1], "text": current_segment.strip()})

                time_parts = line.split("-->")
                if len(time_parts) == 2:
                    start = time_parts[0].strip()
                    end = time_parts[1].strip().split(" ")[0] # Remove potential style info
                    time_line = (start, end)
                    current_segment = "" # Reset text for new segment
                else:
                    time_line = None # Invalid time line
                    current_segment = None
            elif current_segment is not None: # Append text line to current segment
                if current_segment: # Add newline if text already exists
                    current_segment += "\n" + line
                else:
                    current_segment = line

        # Add the last segment
        if current_segment and time_line:
            segments.append({"start": time_line[0], "end": time_line[1], "text": current_segment.strip()})

    except FileNotFoundError:
        print(f"Error: VTT file not found at {vtt_file_path}")
        return None
    except Exception as e:
        print(f"Error parsing VTT file {vtt_file_path}: {e}")
        return None
    return segments


# ---------------------
# PROCESSING FUNCTIONS (Updated)
# ---------------------
def process_subtitle(vtt_file, target_lang_for_translation):
    """Process a VTT subtitle file for translation only."""
    print(f"Processing VTT file: {vtt_file}")
    segments = parse_vtt(vtt_file)
    if segments and target_lang_for_translation:
        # Pass the VTT file itself as the source_file_path for naming convention
        translate_vtt(segments, target_lang_for_translation, source_file_path=vtt_file)
    elif not segments:
         print("Could not parse segments from VTT file.")
    else:
        print("Translation not requested for VTT file.")


def process_audio(
    audio_method,                  # 0=video, 1=YouTube, 2=MP3, 3=VTT-only
    input_path=None,               # Path for file/video/mp3/vtt or Dir
    audio_url=None,                # URL for YouTube
    transcription_method=1,        # 1=API, 2=Local
    target_lang_for_translation=None, # NEW: Target language code ('en', 'ne', etc.) or None
    forced_lang_for_transcription=None # Source language hint
):
    """Main processing function."""

    processed_audio_path = None # Path to the MP3 file used for transcription
    source_identifier = None # Path/URL used for output naming conventions

    # --- Step 1: Get Audio (if not VTT-only) ---
    if audio_method == 0: # Video file
        if not input_path or not os.path.isfile(input_path):
             print(f"Error: Invalid video file path provided: {input_path}")
             return
        source_identifier = input_path
        processed_audio_path = extract_audio_from_video(input_path)
        if not processed_audio_path: return # Stop if extraction failed
    elif audio_method == 1: # YouTube URL
        if not audio_url:
             print("Error: YouTube URL not provided.")
             return
        source_identifier = audio_url # Use URL for context, actual filename comes from download
        processed_audio_path = download_audio(audio_url)
        if not processed_audio_path: return # Stop if download failed
        # Use the actual downloaded filename for output naming
        source_identifier = processed_audio_path
    elif audio_method == 2: # MP3 file
        if not input_path or not os.path.isfile(input_path):
             print(f"Error: Invalid MP3 file path provided: {input_path}")
             return
        source_identifier = input_path
        processed_audio_path = input_path # Use MP3 directly
    elif audio_method == 3: # VTT file (translate only)
        if not input_path or not os.path.isfile(input_path):
            print(f"Error: Invalid VTT file path provided: {input_path}")
            return
        # VTT processing doesn't need transcription, handle translation directly
        process_subtitle(input_path, target_lang_for_translation)
        return # VTT processing ends here
    else:
        print(f"Error: Invalid audio_method specified: {audio_method}")
        return

    # --- Step 2: Transcription (Requires processed_audio_path) ---
    segments = None
    detected_lang = "unknown" # Default
    transcript_path = None # Path to the originally generated transcript

    if processed_audio_path:
        base_name = os.path.splitext(os.path.basename(processed_audio_path))[0]
        # Initial transcript path (before adding language code)
        temp_transcript_path = os.path.join("transcripts", f"original_{base_name}_temp.vtt")

        use_local = (transcription_method == 2)
        segments, detected_lang, temp_transcript_path_actual = transcribe_audio(
            processed_audio_path,
            temp_transcript_path,
            language_code=forced_lang_for_transcription,
            local=use_local
        )

        if segments is None or temp_transcript_path_actual is None:
            print("Transcription failed. Cannot proceed with translation.")
            return

        # Rename transcript file to include detected language
        lang_code = detected_lang if isinstance(detected_lang, str) and detected_lang else "unknown"
        final_transcript_name = f"original_{base_name}_{lang_code}.vtt"
        final_transcript_path = os.path.join("transcripts", final_transcript_name)

        try:
            # Ensure the target directory exists
            os.makedirs(os.path.dirname(final_transcript_path), exist_ok=True)
            # Check if source exists before renaming
            if os.path.exists(temp_transcript_path_actual):
                os.rename(temp_transcript_path_actual, final_transcript_path)
                transcript_path = final_transcript_path # Update path reference
                print(f"Renamed transcript to: {final_transcript_name}")
            else:
                print(f"Warning: Temporary transcript file not found for renaming: {temp_transcript_path_actual}")
                transcript_path = None # Indicate failure

        except OSError as e:
            print(f"Error renaming transcript file from {temp_transcript_path_actual} to {final_transcript_path}: {e}")
            transcript_path = temp_transcript_path_actual # Keep the temp path if rename fails

    else:
        print("Error: No valid audio path obtained for transcription.")
        return


    # --- Step 3: Translation (Requires segments) ---
    if target_lang_for_translation: # Check if a target language was provided
        if segments:
             # Pass the original source identifier (video/audio file path or URL context)
             # for consistent naming of the translated file.
            translate_vtt(segments, target_lang_for_translation, source_file_path=source_identifier)
        else:
            print("Skipping translation because transcription did not produce segments.")
    else:
        print("Translation not requested.")


# ---------------------
# COMMAND-LINE INTERFACE (Updated)
# ---------------------
def main():
    parser = argparse.ArgumentParser(
        description="Tool to process video/audio/subtitle files for transcription and translation.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter # Show defaults in help
    )
    # Input Source Group (Mutually Exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--file", type=str, help="Path to a single input file (video, MP3, or VTT)")
    input_group.add_argument("--dir", type=str, help="Directory containing video files (*.mp4, *.mov) to process")
    input_group.add_argument("--youtube", type=str, help="YouTube video URL (or other yt-dlp supported URL) to download and process")

    # Input Type Flags (Optional - script tries to auto-detect if not provided)
    parser.add_argument("--vtt", action="store_true", help="Force input file interpretation as VTT (for --file only, translation only)")
    parser.add_argument("--mp3", action="store_true", help="Force input file interpretation as MP3 (for --file only)")

    # Processing Options
    parser.add_argument("--local", "-l", action="store_true", help="Use local Whisper model for transcription instead of API")
    # *** UPDATED --translate ***
    parser.add_argument(
        "--translate", "-t",
        nargs='?',                   # 0 or 1 argument allowed
        const="en",                  # Value if flag is present BUT no language code is given
        default=None,                # Value if flag is completely absent
        type=str,
        metavar='LANG_CODE',         # Hint in help message
        help="Translate the text. Defaults to English ('en') if no language code is provided (e.g., 'ne' for Nepali)."
    )
    parser.add_argument("--lang", type=str, metavar='LANG_CODE',
                         help="Hint for SOURCE language of the audio (e.g., 'en', 'ne') for transcription process. Affects Whisper API/model.")

    args = parser.parse_args()

    # --- Determine Processing Parameters ---
    audio_method = -1 # Default invalid
    input_path = None
    audio_url = None

    # Determine transcription method
    # NOTE: --lang only affects transcription source language hint, not translation target.
    forced_lang_for_transcription = args.lang
    transcription_method = 2 if args.local else 1

    # Determine target language for translation (if requested)
    target_lang_for_translation = args.translate # This will be None, 'en', or the specified code ('ne', etc.)

    # Determine Input Method based on provided arguments
    if args.youtube:
        audio_method = 1
        audio_url = args.youtube
        print(f"Processing YouTube URL: {audio_url}")
    elif args.dir:
        # Directory processing - handle this specially
        audio_method = 0 # Will process video files within the loop
        input_path = args.dir
        print(f"Processing video files in directory: {input_path}")
    elif args.file:
        input_path = args.file
        print(f"Processing file: {input_path}")
        # Determine file type for audio_method
        if args.vtt:
            audio_method = 3 # VTT - translate only
        elif args.mp3:
            audio_method = 2 # MP3 - transcribe & maybe translate
        else:
            # Auto-detect based on extension (simple check)
            ext = os.path.splitext(input_path)[1].lower()
            if ext in ['.vtt']:
                 audio_method = 3
                 print("Detected VTT file based on extension.")
                 # Ensure translation is requested if VTT is auto-detected as input
                 if not target_lang_for_translation:
                      print("Warning: VTT file detected, but --translate flag was not provided. No action will be taken.")
                      print("         Use --translate [lang_code] to translate the VTT file.")
                      return # Exit if VTT is input but no translation requested
            elif ext in ['.mp3', '.wav', '.m4a', '.ogg', '.flac']: # Add other audio types if needed
                 audio_method = 2
                 print("Detected audio file based on extension.")
            elif ext in ['.mp4', '.mov', '.avi', '.mkv', '.wmv']: # Add other video types if needed
                 audio_method = 0
                 print("Detected video file based on extension.")
            else:
                 print(f"Error: Cannot determine file type for '{input_path}'. Use --vtt or --mp3 flag to specify.")
                 sys.exit(1)
    else:
         # Should not happen because input_group is required, but good practice
         print("Error: No input source specified (--file, --dir, or --youtube).")
         sys.exit(1)


    # --- Execute Processing ---
    if audio_method == 0 and args.dir: # Directory Processing Loop
        if not os.path.isdir(input_path):
            print(f"Error: Specified directory does not exist: {input_path}")
            sys.exit(1)

        video_extensions = ("*.mp4", "*.mov") # Add more if needed
        files_to_process = []
        for ext in video_extensions:
            files_to_process.extend(glob.glob(os.path.join(input_path, ext)))

        if not files_to_process:
            print(f"No video files ({', '.join(video_extensions)}) found in directory: {input_path}")
            sys.exit(0) # Not an error, just nothing to do

        print(f"Found {len(files_to_process)} video file(s) to process.")
        for file_path in files_to_process:
            print(f"\n--- Processing file: {os.path.basename(file_path)} ---")
            # Call process_audio for each file in the directory
            process_audio(
                audio_method=0, # It's a video file
                input_path=file_path,
                transcription_method=transcription_method,
                target_lang_for_translation=target_lang_for_translation,
                forced_lang_for_transcription=forced_lang_for_transcription
            )
            print(f"--- Finished processing: {os.path.basename(file_path)} ---")

    else: # Single File or URL Processing
        process_audio(
            audio_method=audio_method,
            input_path=input_path, # Will be None if method is 1 (youtube)
            audio_url=audio_url,   # Will be None if method is 0, 2 or 3
            transcription_method=transcription_method,
            target_lang_for_translation=target_lang_for_translation,
            forced_lang_for_transcription=forced_lang_for_transcription
        )

if __name__ == "__main__":
    main()
