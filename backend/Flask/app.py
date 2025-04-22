# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import re
import datetime
import subprocess
import glob
import requests
from datetime import datetime as dt
from dotenv import load_dotenv
import yt_dlp as youtube_dl # Import yt_dlp directly
from google.cloud import translate_v2 as translate # Import google translate
import time # Keep for potential future retry logic if needed
from collections import Counter # Import Counter for keyword extraction
import traceback # For logging full tracebacks

load_dotenv()

app = Flask(__name__)
# Allow all origins for /api/* routes and support credentials
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# --- Constants ---
AUDIO_DIR = "audio_files"
TRANSCRIPTS_DIR = "transcripts" # We still need this to *write* the VTTs temporarily

# ------------------------------------------------------
# Set up Google Translate credentials and OpenAI API key.
# Ensure the path to your Google Cloud credentials JSON file is correct
try:
    # Use expanduser to handle '~' if present
    google_creds_path = os.path.expanduser(
        # --- !!! UPDATE THIS PATH TO YOUR CREDENTIALS FILE !!! ---
        "/Users/tuckr/APIs/Google Cloud/swayambhu-451702-e759a9ee59ab.json"
        # Example alternative: os.path.join(os.path.expanduser("~"), ".config", "gcloud", "application_default_credentials.json")
    )
    if not os.path.exists(google_creds_path):
        raise FileNotFoundError(f"Google Cloud credentials not found at: {google_creds_path}")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_creds_path
    google_client = translate.Client()
    print("Google Translate client initialized successfully.")
except FileNotFoundError as e:
    print(f"Error: {e}")
    print("Google Translate features will be disabled.")
    google_client = None
except Exception as e:
    print(f"Error initializing Google Translate client: {e}")
    print("Google Translate features will be disabled.")
    google_client = None # Indicate that the client is not available

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY environment variable not set. OpenAI transcription will fail.")
# ------------------------------------------------------


# ------------------------------------------------------
# Connect to MongoDB using pymongo:
mongodb_uri = os.getenv("MONGODB_URI")
if not mongodb_uri:
    print("Error: MONGODB_URI environment variable not set.")
    exit(1) # Exit if DB connection is essential

print(f"Attempting to connect to MongoDB at: {mongodb_uri.split('@')[-1] if '@' in mongodb_uri else mongodb_uri}") # Mask credentials in log
try:
    client = MongoClient(mongodb_uri)
    # The ismaster command is cheap and does not require auth. Checks connectivity.
    client.admin.command('ismaster')
    print("MongoDB connection successful.")
    # --- Choose your Database and Collection ---
    db = client["transcript_db"] # Example DB name
    collection = db["media_transcripts"] # Example Collection name
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit(1) # Exit if DB connection is essential
# ------------------------------------------------------

# Create necessary directories if they don't exist
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

# ---------------------
# TEST DB INSERT ROUTE
# ---------------------
@app.route("/api/test-db", methods=["POST"])
def test_db_insert():
    """Inserts test data into the MongoDB collection."""
    if not request.is_json:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
    try:
        result = collection.insert_one(data)
        return jsonify({
            "status": "success",
            "inserted_id": str(result.inserted_id)
        }), 201
    except Exception as e:
        app.logger.error(f"Database insertion failed: {e}")
        return jsonify({
            "status": "error",
            "message": f"An internal server error occurred: {e}"
        }), 500

# ---------------------
# Helper Functions
# ---------------------
def get_timestamp():
    """Returns the current timestamp in YYYYMMDD_HHMMSS format."""
    return dt.now().strftime("%Y%m%d_%H%M%S")

def format_vtt_timestamp(seconds):
    """Converts seconds to VTT timestamp format HH:MM:SS.mmm."""
    if not isinstance(seconds, (int, float)) or seconds < 0:
        seconds = 0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}.{millisecs:03}"

def sanitize_filename(name):
    """Removes or replaces characters unsafe for filenames."""
    if not name:
        name = 'untitled'
    # Remove potentially problematic characters like < > : " / \ | ? * '
    name = re.sub(r'[<>:"/\\|?*\']', '', name)
    # Replace whitespace sequences with a single underscore
    name = re.sub(r'\s+', '_', name)
    # Replace multiple underscores with a single underscore
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores and convert to lowercase
    name = name.strip('_').lower()
    # Limit filename length to prevent issues
    return name[:200]

def safe_delete(file_path):
    """Safely deletes a file if it exists."""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            print(f"Cleaned up: {file_path}")
    except OSError as e:
        print(f"Error deleting file {file_path}: {e.strerror}")
    except Exception as e:
        print(f"Unexpected error deleting file {file_path}: {e}")

# ---------------------
# MEDIA PROCESSING FUNCTIONS
# ---------------------
def extract_audio_from_video(input_path, output_dir=AUDIO_DIR):
    """Extracts audio from a video file using ffmpeg."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input video file not found: {input_path}")

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    sanitized_base_name = sanitize_filename(base_name)
    timestamp = get_timestamp()
    output_audio_filename = f"{sanitized_base_name}_{timestamp}.mp3"
    output_audio_path = os.path.join(output_dir, output_audio_filename)

    command = [
        "ffmpeg", "-i", input_path, "-vn", "-acodec", "mp3",
        "-ar", "44100", "-ac", "2", "-loglevel", "error", output_audio_path
    ]
    try:
        # Added capture_output=True for better error reporting if needed
        process = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Audio extracted successfully to: {output_audio_path}")
        return output_audio_path
    except FileNotFoundError:
        print("Error: 'ffmpeg' command not found. Install ffmpeg and ensure it's in PATH.")
        raise
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg error during audio extraction: {e.stderr}") # Print stderr
        safe_delete(output_audio_path)
        raise RuntimeError(f"ffmpeg failed: {e.stderr}") from e

def download_youtube_audio(url, output_dir=AUDIO_DIR):
    """Downloads audio from a YouTube URL using yt-dlp."""
    timestamp = get_timestamp()
    # Ensure filename template doesn't contain illegal characters before sanitization
    # Using a temporary generic name pattern first, then renaming based on title
    temp_output_template = os.path.join(output_dir, f"youtube_download_{timestamp}.%(ext)s")

    # --- Find ffmpeg path automatically if possible ---
    ffmpeg_location = None
    try:
        # Check common paths or use 'which'/'where'
        result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            ffmpeg_location = result.stdout.strip()
            print(f"Found ffmpeg at: {ffmpeg_location}")
        else: # Try common brew path on mac
             brew_path = '/opt/homebrew/bin/ffmpeg'
             if os.path.exists(brew_path):
                 ffmpeg_location = brew_path
                 print(f"Using ffmpeg at: {ffmpeg_location}")
    except FileNotFoundError:
        pass # 'which' command might not be available

    if not ffmpeg_location:
        print("Warning: ffmpeg location not found automatically. Ensure it's installed and in PATH or set 'ffmpeg_location' manually.")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': temp_output_template, # Use temporary template
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'noplaylist': True,
        'quiet': False, # Set to False for more verbose output if debugging
        'no_warnings': True,
        'restrictfilenames': True, # Helps yt-dlp avoid problematic chars, but we sanitize too
        'writethumbnail': False, # Don't need thumbnail
        'keepvideo': False, # Don't keep original video format
    }
    # Only add ffmpeg_location if found
    if ffmpeg_location:
        ydl_opts['ffmpeg_location'] = ffmpeg_location

    downloaded_file_path = None
    final_audio_path = None
    source_title_base = None

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print(f"Starting YouTube download for: {url}")
            info = ydl.extract_info(url, download=True) # Download happens here

            # Get the actual path of the downloaded *audio* file (after postprocessing)
            downloaded_audio_search_pattern = os.path.join(output_dir, f"youtube_download_{timestamp}.mp3")
            matching_files = glob.glob(downloaded_audio_search_pattern)

            if not matching_files:
                 raise FileNotFoundError(f"Could not find downloaded MP3 matching pattern: '{downloaded_audio_search_pattern}'. Check yt-dlp output.")
            elif len(matching_files) > 1:
                print(f"Warning: Multiple files match {downloaded_audio_search_pattern}. Using first: {matching_files[0]}")
                downloaded_file_path = matching_files[0]
            else:
                downloaded_file_path = matching_files[0]

            # Now rename the downloaded file using the sanitized title
            downloaded_title = info.get('title', 'youtube_audio')
            source_title_base = sanitize_filename(downloaded_title) # Sanitize title for base name
            final_audio_filename = f"{source_title_base}_{timestamp}.mp3"
            final_audio_path = os.path.join(output_dir, final_audio_filename)

            # Rename the file
            os.rename(downloaded_file_path, final_audio_path)
            print(f"YouTube audio downloaded and renamed to: {final_audio_path}")
            print(f"Base name for VTT: {source_title_base}") # Title base is used for VTT base
            return final_audio_path, source_title_base

    except youtube_dl.utils.DownloadError as e:
        print(f"yt-dlp download error: {e}")
        # Clean up partially downloaded file if rename didn't happen
        safe_delete(downloaded_file_path)
        raise RuntimeError(f"Failed to download/process YouTube URL: {url}") from e
    except Exception as e:
        print(f"An unexpected error occurred during YouTube download: {e}")
        # Clean up partially downloaded or renamed file
        safe_delete(downloaded_file_path)
        safe_delete(final_audio_path)
        raise


# ---------------------
# TRANSCRIPTION FUNCTIONS
# ---------------------
def transcribe_audio(audio_path, transcript_output_path, local=False):
    """Transcribes audio using OpenAI Whisper (API or local), saves VTT."""
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found for transcription: {audio_path}")

    segments = None
    detected_language = None

    if local:
        try:
            # Check if whisper is importable first
            try:
                import whisper
            except ImportError:
                print("Error: 'openai-whisper' library not installed. Cannot perform local transcription.")
                print("Install it via pip: pip install -U openai-whisper")
                return None, None

            print("Loading local Whisper model (using 'base', consider size vs performance)...")
            # Consider making model size configurable via env var or parameter
            model = whisper.load_model("base")
            print("Starting local transcription...")
            result = model.transcribe(audio_path, word_timestamps=True, verbose=False) # verbose=False for cleaner logs
            print("Local transcription finished.")

            detected_language = result.get("language", "unknown")
            segments = result.get("segments", [])

            if not segments:
                print("Warning: Local Whisper transcription returned no segments.")
                # Still return language if detected, but segments is empty
                return [], detected_language # Return empty list for segments

            vtt_lines = ["WEBVTT", ""]
            for segment in segments:
                start_time = format_vtt_timestamp(segment["start"])
                end_time = format_vtt_timestamp(segment["end"])
                text = segment["text"].strip()
                vtt_lines.extend([f"{start_time} --> {end_time}", text, ""])

            with open(transcript_output_path, "w", encoding="utf-8") as file:
                file.write("\n".join(vtt_lines))
            print(f"Local transcription saved to: {transcript_output_path}")

        except Exception as e:
            print(f"Local Whisper transcription error: {e}")
            safe_delete(transcript_output_path)
            return None, None # Indicate failure
    else:
        # --- OpenAI API Whisper Transcription ---
        if not OPENAI_API_KEY:
            print("Error: OPENAI_API_KEY not set. Cannot use OpenAI API.")
            return None, None

        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        data = {
            "model": "whisper-1", "response_format": "verbose_json",
            "timestamp_granularities[]": "segment"
        }
        files = {}
        try:
            file_size = os.path.getsize(audio_path)
            max_size = 25 * 1024 * 1024 # 25 MB limit
            if file_size > max_size:
                 print(f"Error: Audio file size ({file_size / (1024*1024):.2f} MB) exceeds OpenAI 25MB limit.")
                 # Consider implementing chunking/splitting here for larger files if needed
                 return None, None

            print(f"Starting OpenAI API transcription for {os.path.basename(audio_path)}...")
            with open(audio_path, "rb") as audio_file:
                files["file"] = (os.path.basename(audio_path), audio_file)
                # Increased timeout, Whisper API can be slow
                response = requests.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers=headers, files=files, data=data, timeout=600 # 10 min timeout
                )
            print(f"OpenAI API response status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                detected_language = result.get("language", "unknown").lower()
                segments = result.get("segments", [])

                if not segments:
                     print("Warning: OpenAI API transcription returned no segments.")
                     safe_delete(transcript_output_path) # Clean up empty temp file
                     # Return empty list for segments, but potentially detected language
                     return [], detected_language

                vtt_lines = ["WEBVTT", ""]
                for segment in segments:
                    start_sec = segment.get("start")
                    end_sec = segment.get("end")
                    text = segment.get("text", "").strip()
                    # Ensure timestamps exist before adding segment
                    if start_sec is not None and end_sec is not None and text:
                        start_time = format_vtt_timestamp(start_sec)
                        end_time = format_vtt_timestamp(end_sec)
                        vtt_lines.extend([f"{start_time} --> {end_time}", text, ""])
                    else:
                        print(f"Warning: Skipping segment with missing timestamp or text: {segment}")

                # Check if any valid lines were added besides the header
                if len(vtt_lines) <= 2:
                    print("Warning: No valid segments with timestamps found after processing.")
                    safe_delete(transcript_output_path)
                    return [], detected_language # Return empty list

                with open(transcript_output_path, "w", encoding="utf-8") as file:
                    file.write("\n".join(vtt_lines))
                print(f"API transcription saved to: {transcript_output_path}")

            else:
                error_details = response.text
                print(f"OpenAI API Error: {response.status_code} - {error_details}")
                safe_delete(transcript_output_path) # Clean up failed attempt
                return None, None # Indicate failure

        except requests.exceptions.Timeout:
             print(f"Network Timeout during OpenAI API request after 600 seconds.")
             safe_delete(transcript_output_path)
             return None, None
        except requests.exceptions.RequestException as e:
            print(f"Network error during OpenAI API request: {e}")
            safe_delete(transcript_output_path)
            return None, None
        except Exception as e:
            print(f"Error during OpenAI API transcription processing: {e}")
            safe_delete(transcript_output_path)
            return None, None # Indicate failure

    # Ensure we return segments (even if empty) and language if transcription was initiated
    return segments, detected_language

# ---------------------
# TRANSLATION FUNCTIONS
# ---------------------
def translate_vtt_segments(segments, target_lang, base_vtt_filename, output_dir=TRANSCRIPTS_DIR):
    """Translates VTT segments using Google Translate and saves a new VTT file."""
    if not google_client:
        print("Error: Google Translate client not available. Skipping translation.")
        return None

    if not segments: # Handle empty segments list gracefully
        print("Warning: No segments provided for translation. Skipping.")
        return None

    # Extract text ensuring segment["text"] exists and is not empty/whitespace
    texts_to_translate = [segment["text"].strip() for segment in segments if segment.get("text", "").strip()]

    if not texts_to_translate:
        print("Warning: No actual text found in segments to translate.")
        return None

    translated_texts = []
    try:
        print(f"Attempting translation of {len(texts_to_translate)} non-empty segments to '{target_lang}'...")
        # Google Translate API can handle lists directly
        # Add a small delay/retry mechanism if hitting quotas frequently
        results = google_client.translate(texts_to_translate, target_language=target_lang)
        translated_texts = [result['translatedText'] for result in results]
        print("Translation successful.")
    except Exception as e: # Catch potential Google API errors
        print(f"Error during Google Translate API call: {e}")
        # Log more details if possible e.g., str(e)
        # Consider adding specific exception handling for common Google API errors if needed
        return None # Indicate translation failure

    if len(translated_texts) != len(texts_to_translate):
         print(f"Warning: Mismatch in count between non-empty original segments ({len(texts_to_translate)}) and translated texts ({len(translated_texts)}). This might indicate partial failure.")
         # Decide how to handle this - proceed with partial results or fail? For now, proceed.

    translated_vtt_filename = f"{base_vtt_filename}_transcription_{target_lang}.vtt"
    translated_vtt_path = os.path.join(output_dir, translated_vtt_filename)

    vtt_lines = ["WEBVTT", ""]
    translation_idx = 0
    original_text_idx = 0
    for segment in segments: # Iterate through original segments to maintain timing
        start_sec = segment.get("start")
        end_sec = segment.get("end")
        original_text = segment.get("text", "").strip()

        # Only process segments that had valid timestamps originally
        if start_sec is None or end_sec is None:
            continue

        start_time = format_vtt_timestamp(start_sec)
        end_time = format_vtt_timestamp(end_sec)

        # Check if the original text was non-empty (and thus should have a translation)
        if original_text:
            if translation_idx < len(translated_texts):
                translated_text = translated_texts[translation_idx]
                vtt_lines.extend([f"{start_time} --> {end_time}", translated_text, ""])
                translation_idx += 1
            else:
                # This case occurs if translation count mismatch happened
                print(f"Warning: Missing translation for segment (originally '{original_text[:30]}...'): {start_time} --> {end_time}")
                # Optionally add placeholder or skip? Adding placeholder for now.
                vtt_lines.extend([f"{start_time} --> {end_time}", "[Translation Failed]", ""])
            original_text_idx += 1 # Increment only when we process a segment that had text
        else:
            # If original segment had no text, add empty line in translation too
             vtt_lines.extend([f"{start_time} --> {end_time}", "", ""])


    # Check if we generated any meaningful content
    if len(vtt_lines) <= 2:
        print(f"Warning: No valid translated segments generated for {target_lang}. Skipping file write.")
        return None

    try:
        with open(translated_vtt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(vtt_lines))
        print(f"Generated translation VTT: {translated_vtt_path}")
        return translated_vtt_path # Return the full path
    except IOError as e:
        print(f"Error writing translated VTT file {translated_vtt_path}: {e}")
        return None


# ------------------------------------------------------------
# HELPER FOR METADATA: Extract Text from VTT String
# (Copied from Part 2)
# ------------------------------------------------------------
def extract_text_from_vtt_string(vtt_content_string):
    """Reads VTT content string and extracts only the spoken text blocks."""
    if not vtt_content_string or not isinstance(vtt_content_string, str):
        return ""
    lines = vtt_content_string.strip().splitlines()
    text_content = []
    # More robust VTT parsing: look for lines *after* a timestamp line
    potential_text_line = False
    for line in lines:
        line = line.strip()
        if line == "" or line.startswith("WEBVTT") or line.startswith("NOTE") or line.startswith("STYLE"):
            potential_text_line = False # Reset if blank or header
            continue
        # Basic timestamp check - assumes standard format
        if re.match(r'^\d{2}:\d{2}:\d{2}\.\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}\.\d{3}', line):
            potential_text_line = True # Line(s) after this might be text
            continue
        if potential_text_line:
            # Assume this line is text until we hit another timestamp or blank line
            # We check again if it looks like a timestamp line itself to avoid multi-line captions being wrongly concatenated
            if not re.match(r'^\d{2}:\d{2}:\d{2}\.\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}\.\d{3}', line):
                 text_content.append(line)
            else:
                 potential_text_line = False # Hit another timestamp, reset

    return " ".join(text_content)

# ------------------------------------------------------------
# HELPER FOR METADATA: Keyword Extraction
# (Copied from Part 2)
# ------------------------------------------------------------
def extract_keywords_from_text(text, num_keywords=10):
    """Extracts simple keywords based on word frequency."""
    if not text: return []
    try:
        # Define stopwords (consider enhancing/customizing, loading from file)
        stopwords = set([
            # English
            "the", "and", "a", "to", "of", "in", "that", "is", "it", "for", "on", "with", "as", "by", "at", "an",
            "this", "or", "be", "are", "was", "were", "i", "you", "he", "she", "we", "they", "my", "your", "his",
            "her", "its", "our", "their", "from", "up", "out", "if", "about", "into", "not", "have", "has", "had",
            "do", "does", "did", "will", "would", "shall", "should", "can", "could", "may", "might", "must", "also",
            "but", "so", "just", "like", "get", "go", "make", "know", "see", "say", "think", "time", "use", "work",
            " K", " G", " M", " T", " s", " m", " pm", " am", # Common units/abbreviations/times
            # Nepali (basic - expand significantly for better results)
            "को", "मा", "छ", "र", "हरु", "यो", "त्यो", "ने", "लागि", "पनि", "एक", "छन्", "गरी", "हो", "के", "छैन",
            "ले", "लाई", "बाट", "त", "भने", "अब", "कि", "संग", "अनि", "गर्नु", "भएको", "भए", "गरेको", "हुन्छ", "तर",
            "यी", "ती", "नै", "जब", "तब", "यहाँ", "त्यहाँ", "कसरी", "किन", "धेरै", "थोरै", "राम्रो", "नराम्रो"
        ])
        # Find sequences of word characters (letters, numbers, underscore)
        # Using \w which includes numbers and underscore. Consider [\p{L}\p{N}_] for broader Unicode support if needed.
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out stopwords, short words (<= 2 chars), and pure numbers
        filtered_words = [w for w in words if w not in stopwords and len(w) > 2 and not w.isdigit()]
        if not filtered_words: return []
        word_freq = Counter(filtered_words)
        # Return the most common words
        common_keywords = [word for word, freq in word_freq.most_common(num_keywords)]
        return common_keywords
    except Exception as e:
         print(f"Error during keyword extraction: {e}")
         return []


# ------------------------------------------------------------
# --- MODIFICATION: New Function for Integrated Metadata Generation ---
# ------------------------------------------------------------
def generate_and_populate_metadata(doc_data):
    """
    Extracts text from VTT, generates keywords, and potentially other metadata,
    updating the provided doc_data dictionary IN PLACE.
    """
    print(f"--- Running automatic metadata generation for job: {doc_data.get('job_id')} ---")
    job_id = doc_data.get("job_id")
    if not job_id:
        print("Warning: Cannot generate metadata without job_id in doc_data.")
        return # Can't proceed

    # --- Get VTT content from the doc_data dictionary ---
    transcript_content_map = doc_data.get("transcript_content", {})
    selected_vtt_content = None
    selected_lang = None

    if not transcript_content_map:
         print(f"Warning: No transcript content available in doc_data for job_id '{job_id}'. Skipping metadata generation.")
         return # Nothing to process

    # --- Select Language for Keyword Extraction ---
    # Priority: 1. Detected Language, 2. English ('en'), 3. Nepali ('ne'), 4. First available
    detected_lang = doc_data.get("detected_language")
    preferred_langs_order = [detected_lang, 'en', 'ne']

    for lang in preferred_langs_order:
        if lang and lang in transcript_content_map:
            selected_lang = lang
            selected_vtt_content = transcript_content_map[lang]
            # Check if content is valid or an error placeholder
            if isinstance(selected_vtt_content, str) and selected_vtt_content.startswith("Error: Could not read file"):
                print(f"Warning: Content for preferred language '{selected_lang}' is an error message. Trying next.")
                selected_vtt_content = None # Reset to try next language
                selected_lang = None
            else:
                break # Found valid content

    # Fallback to the first available language if no preferred language found/valid
    if not selected_lang and transcript_content_map:
        for lang, content in transcript_content_map.items():
             if isinstance(content, str) and not content.startswith("Error: Could not read file"):
                 selected_lang = lang
                 selected_vtt_content = content
                 print(f"Warning: Using first available valid language '{selected_lang}' for keyword extraction.")
                 break

    if not selected_lang or not selected_vtt_content:
        print("Could not select any valid transcript content for keyword extraction. Skipping.")
        # Ensure keywords field exists but is empty
        doc_data['keywords'] = doc_data.get('keywords', []) # Use existing if somehow populated, else empty
        return # Cannot proceed

    print(f"Selected language '{selected_lang}' for keyword extraction.")

    # --- Extract Plain Text ---
    vtt_text_for_keywords = extract_text_from_vtt_string(selected_vtt_content)
    if not vtt_text_for_keywords:
        print("Warning: Could not extract plain text from selected VTT content. Skipping keyword extraction.")
        doc_data['keywords'] = doc_data.get('keywords', [])
        return

    # --- Extract Keywords ---
    keywords = extract_keywords_from_text(vtt_text_for_keywords)
    print(f"Extracted keywords ({len(keywords)}): {keywords}")

    # --- Populate doc_data ---
    # Add/update the 'keywords' field in the dictionary
    doc_data['keywords'] = keywords

    # --- Placeholder for additional automatic metadata extraction ---
    # Example: Infer title from first few lines of text (simple approach)
    if not doc_data.get('title') and vtt_text_for_keywords:
        first_sentence_match = re.match(r"^.*?[.?!]", vtt_text_for_keywords) # Get first sentence
        if first_sentence_match:
            potential_title = first_sentence_match.group(0).strip()
            if len(potential_title) > 10 and len(potential_title) < 100 : # Basic sanity check
                doc_data['title'] = potential_title
                print(f"Inferred title: {potential_title}")

    # Example: Simple summary (first N words) - USE LLM FOR BETTER RESULTS
    if not doc_data.get('summary') and vtt_text_for_keywords:
         words = vtt_text_for_keywords.split()
         potential_summary = " ".join(words[:50]) + ("..." if len(words) > 50 else "")
         doc_data['summary'] = potential_summary
         print(f"Generated simple summary (first 50 words).")

    # Add more logic here for speaker, location, category detection if needed
    # Simple regex examples (less reliable than dedicated models):
    if not doc_data.get('location') and vtt_text_for_keywords:
        # Look for patterns like "in Kathmandu", "at Swayambhu" etc.
        loc_match = re.search(r'\b(?:in|at|near)\s+([A-Z][A-Za-z\s\-]+)\b', vtt_text_for_keywords)
        if loc_match:
            doc_data['location'] = f"Possibly: {loc_match.group(1).strip()}"
            print(f"Inferred location: {doc_data['location']}")

    if not doc_data.get('speaker') and vtt_text_for_keywords:
         # Look for patterns like "Speaker: John Doe", "by Jane Smith"
        sp_match = re.search(r'\b(?:by|from|speaker[:]?|voiced by)\s+([A-Z][A-Za-z\s\.\-]+)\b', vtt_text_for_keywords) # Look for capitalized names
        if sp_match:
            doc_data['speaker'] = f"Possibly: {sp_match.group(1).strip()}"
            print(f"Inferred speaker: {doc_data['speaker']}")

    print(f"--- Finished automatic metadata generation for job: {job_id} ---")
    # doc_data is modified in place, no need to return it


# ---------------------
# MAIN PROCESSING ENDPOINT (Storing VTT Content)
# ---------------------
@app.route("/api/generate-transcription", methods=["POST", "OPTIONS"])
def generate_transcription_endpoint():
    """
    Handles media processing, transcription, translation,
    and stores VTT *content* in the database. Deletes local VTT files afterwards.
    Optionally generates and adds further metadata based on a request parameter.
    """
    if request.method == "OPTIONS":
        # Handle CORS preflight request
        response = jsonify({"message": "Preflight OK"})
        # Ensure CORS headers are set correctly for OPTIONS response if not handled globally
        return response, 200

    # --- Initialize variables ---
    source_type = None
    source = None
    original_media_name = None
    vtt_base_filename = None
    uploaded_file_path = None
    should_generate_metadata = False
    use_local_whisper = False
    files_to_clean = []
    processed_audio_path = None
    final_transcript_path = None
    translation_paths = {}
    doc_data = {} # Initialize doc_data dictionary

    try:
        timestamp = get_timestamp() # Generate timestamp early

        # --- 1. Determine Input Type and Get Raw Source ---
        if request.is_json:
            data = request.json
            if not data:
                 return jsonify({"status": "error", "message": "Received JSON content type but empty request body"}), 400

            source_type = data.get("source_type", "").lower()
            source = data.get("source", "")

            # Get flags from JSON
            raw_gen_meta = data.get("generate_metadata", False)
            should_generate_metadata = str(raw_gen_meta).lower() == 'true' if isinstance(raw_gen_meta, str) else bool(raw_gen_meta)
            raw_local = data.get("local_transcription", False)
            use_local_whisper = str(raw_local).lower() == 'true' if isinstance(raw_local, str) else bool(raw_local)

            if not source_type or not source:
                 return jsonify({"status": "error", "message": "Missing 'source_type' or 'source' in JSON body"}), 400
            if source_type not in ["youtube", "mp4"]:
                 return jsonify({"status": "error", "message": f"Invalid 'source_type' '{source_type}'. Must be 'youtube' or 'mp4'."}), 400

            original_media_name = source

        elif request.files: # Multipart Form Data
            source_type = request.form.get("source_type", "").lower()
            source_input = request.files.get("source")

            # Get flags from Form Data
            should_generate_metadata = request.form.get("generate_metadata", 'false').lower() == 'true'
            use_local_whisper = request.form.get("local_transcription", 'false').lower() == 'true'

            if not source_type or not source_input:
                 return jsonify({"status": "error", "message": "Missing 'source_type' form field or 'source' file"}), 400
            if source_type != "mp4":
                 return jsonify({"status": "error", "message": f"Invalid source_type '{source_type}' for file upload. Only 'mp4' supported."}), 400

            original_filename = source_input.filename
            if not original_filename:
                 return jsonify({"status": "error", "message": "Uploaded file has no filename."}), 400

            uploaded_file_extension = os.path.splitext(original_filename)[1].lower()
            allowed_extensions = {'.mp4'}
            if uploaded_file_extension not in allowed_extensions:
                 return jsonify({"status": "error", "message": f"Unsupported file extension '{uploaded_file_extension}'. Only .mp4 allowed."}), 400

            sanitized_original_filename_base = sanitize_filename(os.path.splitext(original_filename)[0])
            uploaded_file_path = os.path.join(AUDIO_DIR, f"{sanitized_original_filename_base}_{timestamp}{uploaded_file_extension}")

            try:
                source_input.save(uploaded_file_path)
                print(f"Saved uploaded file temporarily to: {uploaded_file_path}")
            except Exception as e:
                 print(f"Error saving uploaded file: {e}")
                 safe_delete(uploaded_file_path)
                 return jsonify({"status": "error", "message": f"Failed to save uploaded file: {e}"}), 500

            source = uploaded_file_path
            original_media_name = original_filename
            files_to_clean.append(uploaded_file_path)

        else:
             return jsonify({"status": "error", "message": "Request must be JSON or multipart/form-data"}), 415

        print(f"Processing request: source_type='{source_type}', source='{source}', "
              f"generate_metadata={should_generate_metadata}, use_local_whisper={use_local_whisper}")

        # --- 2. Process Source and Derive Names ---
        if source_type == "youtube":
            processed_audio_path, source_title_base = download_youtube_audio(source, AUDIO_DIR)
            vtt_base_filename = f"{source_title_base}_{timestamp}"
            files_to_clean.append(processed_audio_path)
        elif source_type == "mp4":
             input_mp4_path = source
             if not os.path.exists(input_mp4_path):
                  raise FileNotFoundError(f"Input MP4 file not found or inaccessible: {input_mp4_path}")
             processed_audio_path = extract_audio_from_video(input_mp4_path, AUDIO_DIR)
             files_to_clean.append(processed_audio_path)
             original_name_base_for_vtt = sanitize_filename(os.path.splitext(os.path.basename(original_media_name))[0])
             vtt_base_filename = f"{original_name_base_for_vtt}_{timestamp}"

        if not processed_audio_path or not vtt_base_filename or not original_media_name:
             raise RuntimeError("Audio processing failed: Could not determine processed audio path or base filename.")

        # --- 3. Transcribe Audio ---
        temp_transcript_path = os.path.join(TRANSCRIPTS_DIR, f"{vtt_base_filename}_transcription_temp.vtt")
        segments, detected_lang = transcribe_audio(processed_audio_path, temp_transcript_path, local=use_local_whisper)

        if segments is None or detected_lang is None:
            raise RuntimeError(f"Audio transcription failed for job: {vtt_base_filename}")

        lang_standardization_map = {'english': 'en', 'en': 'en', 'nepali': 'ne', 'ne': 'ne'}
        standardized_lang = lang_standardization_map.get(detected_lang.lower(), detected_lang.lower())
        print(f"Detected language: '{detected_lang}', Standardized to: '{standardized_lang}'")

        final_transcript_filename = f"{vtt_base_filename}_transcription_{standardized_lang}.vtt"
        final_transcript_path = os.path.join(TRANSCRIPTS_DIR, final_transcript_filename)

        if os.path.exists(temp_transcript_path):
            try:
                os.rename(temp_transcript_path, final_transcript_path)
                print(f"Created original transcript: {final_transcript_path}")
                files_to_clean.append(final_transcript_path)
            except OSError as e:
                print(f"Error renaming temporary transcript file: {e}")
                files_to_clean.append(temp_transcript_path)
                raise RuntimeError("Failed to finalize transcript filename.")
        elif not segments:
             print("Warning: Transcription resulted in empty segments. No transcript file generated.")
             final_transcript_path = None
        else:
             print(f"Error: Transcription segments found, but temp file '{temp_transcript_path}' does not exist.")
             raise RuntimeError("Transcription inconsistency: segments exist but temp file missing.")

        # --- 4. Generate Translations ---
        target_langs = []
        if standardized_lang == 'en': target_langs.append('ne')
        elif standardized_lang == 'ne': target_langs.append('en')
        else: target_langs.extend(['en', 'ne'])

        if not google_client:
             print("Skipping translation: Google client not available.")
        elif not segments:
              print("Skipping translation: No segments available from transcription.")
        else:
            for lang_code in target_langs:
                translated_vtt_path = translate_vtt_segments(segments, lang_code, vtt_base_filename, TRANSCRIPTS_DIR)
                if translated_vtt_path:
                    translation_paths[lang_code] = translated_vtt_path
                    files_to_clean.append(translated_vtt_path)
                else:
                    print(f"Translation to '{lang_code}' failed or produced no output.")

        # --- 5. Read VTT Content and Prepare Base DB Data ---
        db_transcript_content = {}
        content_read_errors = []

        if final_transcript_path and standardized_lang:
            try:
                with open(final_transcript_path, "r", encoding="utf-8") as f:
                    db_transcript_content[standardized_lang] = f.read()
            except Exception as e:
                err_msg = f"Error reading original transcript ({standardized_lang}) {final_transcript_path}: {e}"
                print(err_msg)
                content_read_errors.append(err_msg)
                db_transcript_content[standardized_lang] = f"Error: Could not read file content. {e}"

        for lang, path in translation_paths.items():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    db_transcript_content[lang] = f.read()
            except Exception as e:
                err_msg = f"Error reading translated transcript ({lang}) {path}: {e}"
                print(err_msg)
                content_read_errors.append(err_msg)
                db_transcript_content[lang] = f"Error: Could not read file content. {e}"

        # --- Prepare base document data dictionary ---
        doc_data = {
            "job_id": vtt_base_filename,
            "source_type": source_type,
            "source_location": original_media_name,
            "processing_timestamp": timestamp,
            "detected_language": standardized_lang,
            "transcript_content": db_transcript_content,
            "url": original_media_name if source_type == "youtube" else None,
            "processing_info": {
                "processed_at": dt.now().isoformat(),
                "transcription_method": "local" if use_local_whisper else "openai_api",
                "temp_audio_file": os.path.basename(processed_audio_path) if processed_audio_path else None,
                "temp_original_transcript_file": os.path.basename(final_transcript_path) if final_transcript_path else None,
                "temp_translated_transcript_files": {lang: os.path.basename(p) for lang, p in translation_paths.items()},
                "temp_uploaded_file": os.path.basename(uploaded_file_path) if uploaded_file_path else None,
            },
            # Initialize descriptive metadata fields (might be populated by generate_and_populate_metadata)
            "date_added": None,
            "location": None,
            "speaker": None,
            "category": None, # Renamed 'type' to 'category'
            "keywords": [],
            "title": None,
            "summary": None,
            "last_updated": None, # Will be set before DB write
        }
        if content_read_errors:
             doc_data["processing_info"]["content_read_errors"] = content_read_errors

        # --- 6. CONDITIONAL: Generate Additional Metadata ---
        if should_generate_metadata:
            print(f"Flag 'generate_metadata' is True. Calling metadata generation function for job: {vtt_base_filename}")
            try:
                # --- MODIFICATION: Call the integrated metadata generation function ---
                generate_and_populate_metadata(doc_data) # Modifies doc_data in place
                # --- End MODIFICATION ---
            except Exception as e:
                print(f"Error during metadata generation step: {e}")
                traceback.print_exc() # Log full traceback for metadata errors
                # Store error in processing info, but don't halt the process
                doc_data["processing_info"]["metadata_generation_error"] = str(e)
        else:
             print(f"Flag 'generate_metadata' is False. Skipping automatic metadata generation.")

        # --- 7. Insert or Update in DB ---
        existing = collection.find_one({"job_id": vtt_base_filename})
        current_iso_time = dt.now().isoformat()
        doc_data["last_updated"] = current_iso_time # Set last updated time

        if existing:
            print(f"Updating DB entry for job_id: {vtt_base_filename}")
            # Prepare update payload - basically, update everything except maybe date_added
            update_payload = doc_data.copy() # Start with all fields from doc_data
            if "date_added" in update_payload:
                 del update_payload["date_added"] # Don't overwrite existing date_added on update

            # Use the existing _id for the update query
            update_result = collection.update_one(
                 {"_id": existing["_id"]},
                 {"$set": update_payload} # Update all fields based on current processing run
             )
            db_status = "updated" if update_result.modified_count > 0 else "no change"
            inserted_id = str(existing["_id"])

        else:
            print(f"Creating new DB entry for job_id: {vtt_base_filename}")
            # Set date_added only on initial creation
            doc_data["date_added"] = current_iso_time
            insert_result = collection.insert_one(doc_data) # Insert the full doc_data
            if insert_result.inserted_id:
                 db_status = "created"
                 inserted_id = str(insert_result.inserted_id)
            else:
                 db_status = "creation failed"
                 inserted_id = None
                 raise RuntimeError("Database insertion failed unexpectedly.")

        # --- 8. Cleanup Temporary Files ---
        print("Performing cleanup (deleting temporary audio and VTT files)...")
        for path in files_to_clean:
            safe_delete(path)

        # --- 9. Return Success Response ---
        response_data = {
            "status": db_status,
            "job_id": vtt_base_filename,
            "detected_language": standardized_lang,
            "message": f"Processing complete for {original_media_name}. Status: {db_status}.",
            "inserted_or_updated_id": inserted_id,
            "transcript_en": db_transcript_content.get('en', '')[:100] + "..." if db_transcript_content.get('en') else "N/A",
            "transcript_ne": db_transcript_content.get('ne', '')[:100] + "..." if db_transcript_content.get('ne') else "N/A",
            "filename": original_media_name
        }
        return jsonify(response_data), 200 if db_status in ["created", "updated", "no change"] else 500

    # --- Error Handling ---
    except FileNotFoundError as e:
        print(f"Error - File Not Found: {e}")
        for path in files_to_clean: safe_delete(path)
        return jsonify({"status": "error", "message": f"File not found or inaccessible: {e}"}), 404
    except youtube_dl.utils.DownloadError as e:
        print(f"Error - YouTube Download Failed: {e}")
        for path in files_to_clean: safe_delete(path)
        return jsonify({"status": "error", "message": f"YouTube download failed: {e}"}), 500
    except RuntimeError as e:
        print(f"Error - Processing Runtime Error: {e}")
        for path in files_to_clean: safe_delete(path)
        return jsonify({"status": "error", "message": f"Processing error: {e}"}), 500
    except Exception as e:
        print(f"Error - Unexpected Internal Server Error: {e}")
        traceback.print_exc() # Log full traceback for unexpected errors
        for path in files_to_clean: safe_delete(path)
        return jsonify({"status": "error", "message": f"An unexpected internal server error occurred: {e}"}), 500


# ------------------------------------------------------------
# --- MODIFICATION: Comment out the old separate metadata endpoint ---
# --- This can be repurposed for MANUAL updates later if needed ---
# ------------------------------------------------------------
# @app.route("/api/generate-metadata", methods=["POST", "OPTIONS"])
# def generate_metadata_endpoint_old():
#     """
#     (DISABLED - Logic integrated into main endpoint)
#     Updates metadata for a job, extracting keywords from VTT content stored in DB.
#     """
#     if request.method == "OPTIONS": return jsonify({"message": "Preflight OK"}), 200
#     if not request.is_json: return jsonify({"status": "error", "message": "Request must be JSON"}), 400

#     data = request.json
#     job_id = data.get("job_id")
#     # Fields for manual update
#     url_field = data.get("url")
#     location = data.get("location")
#     speaker = data.get("speaker")
#     category = data.get("category") # Use category instead of type
#     lang_for_keywords = data.get("keyword_language")

#     if not job_id: return jsonify({"error": "'job_id' is required"}), 400

#     doc = collection.find_one({"job_id": job_id})
#     if not doc: return jsonify({"error": f"No entry found for job_id '{job_id}'."}), 404

#     # --- Prepare updates based on request data ---
#     updates_to_set = {}
#     if url_field is not None: updates_to_set["url"] = url_field
#     if location is not None: updates_to_set["location"] = location
#     if speaker is not None: updates_to_set["speaker"] = speaker
#     if category is not None: updates_to_set["category"] = category # Update category

#     # --- Keyword Extraction (if VTT content exists) ---
#     transcript_content_map = doc.get("transcript_content", {})
#     selected_vtt_content = None
#     selected_lang = None

#     if transcript_content_map:
#         # Select language based on request or fallbacks
#         if lang_for_keywords and lang_for_keywords in transcript_content_map:
#             selected_lang = lang_for_keywords
#         elif doc.get("detected_language") in transcript_content_map:
#             selected_lang = doc["detected_language"]
#         elif transcript_content_map:
#             selected_lang = next(iter(transcript_content_map))

#         if selected_lang:
#             selected_vtt_content = transcript_content_map[selected_lang]
#             if isinstance(selected_vtt_content, str) and not selected_vtt_content.startswith("Error:"):
#                  vtt_text_for_keywords = extract_text_from_vtt_string(selected_vtt_content)
#                  if vtt_text_for_keywords:
#                      keywords = extract_keywords_from_text(vtt_text_for_keywords)
#                      updates_to_set["keywords"] = keywords
#                      print(f"Extracted keywords ({len(keywords)}) for manual update request: {keywords}")

#     # Add last updated timestamp
#     updates_to_set["last_updated"] = dt.now().isoformat()

#     # --- Perform DB Update ---
#     if not updates_to_set:
#          return jsonify({"status": "no update needed", "job_id": job_id, "message": "No metadata fields provided for update."})
#     try:
#         result = collection.update_one({"_id": doc["_id"]}, {"$set": updates_to_set})
#         status = "metadata updated" if result.modified_count > 0 else "metadata unchanged"
#         print(f"Manual metadata update status for job_id {job_id}: {status}")
#         return jsonify({"status": status, "job_id": job_id, "updated_fields": list(updates_to_set.keys())})
#     except Exception as e:
#         app.logger.error(f"Error during manual metadata update for job_id {job_id}: {e}")
#         return jsonify({"status": "error", "message": f"Database update failed: {e}"}), 500


# --- Main Execution ---
if __name__ == "__main__":
    print(f"Starting Flask server at {dt.now().isoformat()}...")
    print(f"Audio Directory: {os.path.abspath(AUDIO_DIR)}")
    print(f"Transcripts Directory: {os.path.abspath(TRANSCRIPTS_DIR)}")
    print(f"Google Translate Client Available: {'Yes' if google_client else 'No'}")
    print(f"OpenAI API Key Set: {'Yes' if OPENAI_API_KEY else 'No'}")
    # Set debug=True for development (enables auto-reload and detailed errors)
    # Set debug=False for production deployment
    app.run(host="0.0.0.0", port=5000, debug=True)