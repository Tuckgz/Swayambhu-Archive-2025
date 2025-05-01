# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId # Needed for working with MongoDB document IDs
import os
import re
import datetime
import subprocess
import glob
import requests
from datetime import datetime as dt # Keep datetime as dt for consistency
from dotenv import load_dotenv
import yt_dlp as youtube_dl
from google.cloud import translate_v2 as translate
import time
from collections import Counter
import traceback

load_dotenv()

app = Flask(__name__)
# Allow all origins for /api/* routes and support credentials
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# --- Constants ---
AUDIO_DIR = "audio_files"
TRANSCRIPTS_DIR = "transcripts"

# ------------------------------------------------------
# Set up Google Translate credentials and OpenAI API key.
try:
    google_creds_path = os.path.expanduser(
        # --- !!! UPDATE THIS PATH TO YOUR CREDENTIALS FILE !!! ---
        "/Users/tuckr/APIs/Google Cloud/swayambhu-451702-e759a9ee59ab.json"
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
    google_client = None

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY environment variable not set. OpenAI transcription will fail.")
# ------------------------------------------------------


# ------------------------------------------------------
# Connect to MongoDB using pymongo:
mongodb_uri = os.getenv("MONGODB_URI")
if not mongodb_uri:
    print("Error: MONGODB_URI environment variable not set.")
    exit(1)

print(f"Attempting to connect to MongoDB at: {mongodb_uri.split('@')[-1] if '@' in mongodb_uri else mongodb_uri}")
try:
    client = MongoClient(mongodb_uri)
    client.admin.command('ismaster')
    print("MongoDB connection successful.")
    db = client["transcript_db"]
    collection = db["media_transcripts"]
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit(1)
# ------------------------------------------------------

# Create necessary directories if they don't exist
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

# ------------------------------------------------------------
# Define allowed search fields (matching frontend for validation)
# Consider keeping this in sync with your frontend ManageContentCard.tsx
# ------------------------------------------------------------
allowed_search_fields = [
    "title",
    "source_location",
    "keywords",
    "speaker",
    "job_id",
    # Add more fields if needed, matching frontend searchFields
]


# ---------------------
# TEST DB INSERT ROUTE (from part 1)
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


# ------------------------------------------------------------
# --- NEW ENDPOINT: Search Content ---
# ------------------------------------------------------------
@app.route("/api/search-content", methods=["GET"])
def search_content():
    """
    Searches for content items in the database based on a field and query.
    Supports searching by: title, source_location, keywords, speaker, job_id.
    Returns a list of matching content items.
    """
    field = request.args.get("field")
    query = request.args.get("query")

    if not field or not query:
        return jsonify({"status": "error", "message": "Missing 'field' or 'query' parameters"}), 400

    # Ensure the requested field is one of the allowed search fields
    if field not in allowed_search_fields:
         return jsonify({"status": "error", "message": f"Invalid search field: {field}"}), 400

    # Build the search query for MongoDB
    mongo_query = {}
    search_term = query.strip()

    if not search_term:
         return jsonify({"status": "error", "message": "Search query cannot be empty"}), 400

    try:
        if field == 'job_id':
            # Exact match for job_id
            mongo_query = {field: search_term}
        elif field == 'keywords':
            # For keywords (an array), search if the array *contains* the search term.
            # This performs an exact match check against array elements.
            # If you need substring search within keywords, you might use a text index
            # or iterate through the array with regex ($elemMatch + $regex), but the latter can be slow.
            mongo_query = {field: search_term}
        elif field in ['title', 'source_location', 'speaker']:
             # Case-insensitive substring search for string fields
             mongo_query = {field: {"$regex": search_term, "$options": "i"}}
        # Add other field types/search logic here if needed (e.g., exact match for category, language)
        # elif field == 'category':
        #      mongo_query = {field: search_term} # Exact match for category

        app.logger.info(f"Executing search query: {mongo_query}")

        # Execute the query
        # Use a limit to prevent fetching too many results, can add pagination later
        # Also sort to get a consistent order, e.g., by date added descending
        results = list(collection.find(mongo_query).sort("date_added", -1).limit(100)) # Limit to 100 results, sort by date

        # Prepare results for JSON response
        # Convert ObjectId to string and handle potential nulls
        # Ensure all expected fields from ContentItem are present, even if null, for frontend typing
        content_list = []
        for doc in results:
            # Create a dictionary mirroring the ContentItem structure expected by the frontend
            item = {
                '_id': str(doc.get('_id')),
                'job_id': doc.get('job_id'),
                'title': doc.get('title'),
                'url': doc.get('url'),
                'source_location': doc.get('source_location'),
                'source_type': doc.get('source_type'),
                'speaker': doc.get('speaker'),
                'location': doc.get('location'),
                'category': doc.get('category'),
                'keywords': doc.get('keywords', []), # Ensure keywords is always a list, default to empty
                'detected_language': doc.get('detected_language'),
                # Convert datetime objects to ISO format strings
                'date_added': doc.get('date_added').isoformat() if isinstance(doc.get('date_added'), datetime.datetime) else doc.get('date_added'),
                'last_updated': doc.get('last_updated').isoformat() if isinstance(doc.get('last_updated'), datetime.datetime) else doc.get('last_updated'),
                'processing_info': doc.get('processing_info', {}) # Ensure processing_info is an object, default to empty
                # Add other fields from your schema here that the frontend expects
            }
            content_list.append(item)

        app.logger.info(f"Found {len(results)} results for query '{query}' in field '{field}'")
        return jsonify(content_list), 200

    except Exception as e:
        app.logger.error(f"Error during search: {e}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": "An internal server error occurred during search"}), 500

# ------------------------------------------------------------
# --- NEW ENDPOINT: Update Content ---
# ------------------------------------------------------------
@app.route("/api/update-content/<string:doc_id>", methods=["PUT"])
def update_content(doc_id):
    """
    Updates a specific content item in the database.
    Expects JSON payload with fields to update (matching frontend EditFormData structure,
    but keywords should be string[] in payload).
    """
    if not request.is_json:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 415

    update_data = request.get_json()

    if not isinstance(update_data, dict):
        return jsonify({"status": "error", "message": "Invalid data format, expected JSON object"}), 400

    if not doc_id:
        # This check is mostly redundant due to the route definition but harmless
        return jsonify({"status": "error", "message": "Document ID not provided in URL"}), 400

    try:
        # Convert doc_id string to MongoDB ObjectId
        object_id = ObjectId(doc_id)
    except Exception:
        return jsonify({"status": "error", "message": "Invalid Document ID format"}), 400

    # Prepare the update document using $set
    # Use the received JSON data directly for $set.
    # The frontend is responsible for sending the correct format (e.g., keywords as string[]).
    update_document = {"$set": update_data}

    # Always update the last_updated timestamp
    update_document["$set"]["last_updated"] = dt.now()

    # Ensure required fields like job_id, source_location, source_type are not accidentally removed
    # by the update if they weren't included in the frontend payload.
    # A more robust approach might merge existing data with update_data,
    # but assuming frontend only sends editable fields, $set is fine if non-editable
    # fields are not present in update_data. Let's add a check/logging for safety.
    non_editable_required_fields = ['job_id', 'source_location', 'source_type']
    for field in non_editable_required_fields:
        if field in update_data:
            # This shouldn't happen if frontend only sends editable fields, but log if it does
            app.logger.warning(f"Received unexpected non-editable field '{field}' in update payload for {doc_id}.")
            # Optionally remove it from update_data if you strictly forbid updating these
            # del update_data[field]
            # Or let $set update it if it's harmless (e.g., rewriting same value)

    app.logger.info(f"Attempting to update document ID: {doc_id} with data: {update_data}")

    try:
        # Perform the update operation
        result = collection.update_one({"_id": object_id}, update_document)

        if result.matched_count == 0:
            return jsonify({"status": "error", "message": f"Document with ID {doc_id} not found"}), 404
        elif result.modified_count == 0:
             # Matched but not modified - data was likely identical
             app.logger.info(f"Document ID {doc_id} matched but not modified.")
             # Fetch and return the current document state
             updated_doc = collection.find_one({"_id": object_id})
             if updated_doc:
                 # Format the document for the frontend response
                  item = {
                    '_id': str(updated_doc.get('_id')),
                    'job_id': updated_doc.get('job_id'),
                    'title': updated_doc.get('title'),
                    'url': updated_doc.get('url'),
                    'source_location': updated_doc.get('source_location'),
                    'source_type': updated_doc.get('source_type'),
                    'speaker': updated_doc.get('speaker'),
                    'location': updated_doc.get('location'),
                    'category': updated_doc.get('category'),
                    'keywords': updated_doc.get('keywords', []),
                    'detected_language': updated_doc.get('detected_language'),
                    'date_added': updated_doc.get('date_added').isoformat() if isinstance(updated_doc.get('date_added'), datetime.datetime) else updated_doc.get('date_added'),
                    'last_updated': updated_doc.get('last_updated').isoformat() if isinstance(updated_doc.get('last_updated'), datetime.datetime) else updated_doc.get('last_updated'),
                    'processing_info': updated_doc.get('processing_info', {})
                  }
                  return jsonify(item), 200
             else:
                  app.logger.warning(f"Document ID {doc_id} matched but not found when attempting to retrieve after no modification.")
                  return jsonify({"status": "warning", "message": f"Document with ID {doc_id} matched but could not be retrieved after no modification."}), 404

        else: # Successfully modified (result.modified_count > 0)
            app.logger.info(f"Document ID {doc_id} updated successfully ({result.modified_count} modified).")
            # Fetch and return the updated document to ensure frontend state is correct
            updated_doc = collection.find_one({"_id": object_id})
            if updated_doc:
                 # Format the document for the frontend response
                 item = {
                    '_id': str(updated_doc.get('_id')),
                    'job_id': updated_doc.get('job_id'),
                    'title': updated_doc.get('title'),
                    'url': updated_doc.get('url'),
                    'source_location': updated_doc.get('source_location'),
                    'source_type': updated_doc.get('source_type'),
                    'speaker': updated_doc.get('speaker'),
                    'location': updated_doc.get('location'),
                    'category': updated_doc.get('category'),
                    'keywords': updated_doc.get('keywords', []),
                    'detected_language': updated_doc.get('detected_language'),
                    'date_added': updated_doc.get('date_added').isoformat() if isinstance(updated_doc.get('date_added'), datetime.datetime) else updated_doc.get('date_added'),
                    'last_updated': updated_doc.get('last_updated').isoformat() if isinstance(updated_doc.get('last_updated'), datetime.datetime) else updated_doc.get('last_updated'),
                    'processing_info': updated_doc.get('processing_info', {})
                 }
                 return jsonify(item), 200
            else:
                app.logger.error(f"Document ID {doc_id} modified but could not be retrieved after update.")
                return jsonify({"status": "error", "message": f"Document with ID {doc_id} updated but failed to retrieve."}), 500


    except Exception as e:
        app.logger.error(f"Error during update for document ID {doc_id}: {e}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": "An internal server error occurred during update"}), 500


# ---------------------
# Helper Functions (from part 1 and 2)
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
# MEDIA PROCESSING FUNCTIONS (from part 1)
# ---------------------
def extract_audio_from_video(input_path, output_dir=AUDIO_DIR):
    """Extracts audio from a video file using ffmpeg."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input video file not found: {input_path}")

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    sanitized_base_name = sanitize_filename(base_name)
    timestamp = get_timestamp() # Re-generate timestamp here for filename uniqueness if needed, or use one from main function
    output_audio_filename = f"{sanitized_base_name}_{timestamp}.mp3"
    output_audio_path = os.path.join(output_dir, output_audio_filename)

    command = [
        "ffmpeg", "-i", input_path, "-vn", "-acodec", "mp3",
        "-ar", "44100", "-ac", "2", "-loglevel", "error", output_audio_path
    ]
    try:
        process = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Audio extracted successfully to: {output_audio_path}")
        return output_audio_path
    except FileNotFoundError:
        print("Error: 'ffmpeg' command not found. Install ffmpeg and ensure it's in PATH.")
        raise
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg error during audio extraction: {e.stderr}")
        safe_delete(output_audio_path)
        raise RuntimeError(f"ffmpeg failed: {e.stderr}") from e

def download_youtube_audio(url, output_dir=AUDIO_DIR):
    """Downloads audio from a YouTube URL using yt-dlp."""
    timestamp = get_timestamp() # Re-generate timestamp here
    temp_output_template = os.path.join(output_dir, f"youtube_download_{timestamp}.%(ext)s")

    ffmpeg_location = None
    try:
        result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            ffmpeg_location = result.stdout.strip()
            print(f"Found ffmpeg at: {ffmpeg_location}")
        else:
             brew_path = '/opt/homebrew/bin/ffmpeg' # Common path on macOS Homebrew
             if os.path.exists(brew_path):
                 ffmpeg_location = brew_path
                 print(f"Using ffmpeg at: {ffmpeg_location}")
    except FileNotFoundError:
        pass

    if not ffmpeg_location:
        print("Warning: ffmpeg location not found automatically. Ensure it's installed and in PATH or set 'ffmpeg_location' manually in download_youtube_audio.")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': temp_output_template,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'noplaylist': True,
        'quiet': False,
        'no_warnings': True,
        'restrictfilenames': True,
        'writethumbnail': False,
        'keepvideo': False,
    }
    if ffmpeg_location:
        ydl_opts['ffmpeg_location'] = ffmpeg_location

    downloaded_file_path = None
    final_audio_path = None
    source_title_base = None

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print(f"Starting YouTube download for: {url}")
            info = ydl.extract_info(url, download=True)

            downloaded_audio_search_pattern = os.path.join(output_dir, f"youtube_download_{timestamp}.mp3")
            matching_files = glob.glob(downloaded_audio_search_pattern)

            if not matching_files:
                 raise FileNotFoundError(f"Could not find downloaded MP3 matching pattern: '{downloaded_audio_search_pattern}'. Check yt-dlp output.")
            elif len(matching_files) > 1:
                print(f"Warning: Multiple files match {downloaded_audio_search_pattern}. Using first: {matching_files[0]}")
                downloaded_file_path = matching_files[0]
            else:
                downloaded_file_path = matching_files[0]

            downloaded_title = info.get('title', 'youtube_audio')
            source_title_base = sanitize_filename(downloaded_title)
            final_audio_filename = f"{source_title_base}_{timestamp}.mp3"
            final_audio_path = os.path.join(output_dir, final_audio_filename)

            os.rename(downloaded_file_path, final_audio_path)
            print(f"YouTube audio downloaded and renamed to: {final_audio_path}")
            print(f"Base name for VTT: {source_title_base}")
            return final_audio_path, source_title_base

    except youtube_dl.utils.DownloadError as e:
        print(f"yt-dlp download error: {e}")
        safe_delete(downloaded_file_path)
        raise RuntimeError(f"Failed to download/process YouTube URL: {url}") from e
    except Exception as e:
        print(f"An unexpected error occurred during YouTube download: {e}")
        safe_delete(downloaded_file_path)
        safe_delete(final_audio_path)
        raise


# ---------------------
# TRANSCRIPTION FUNCTIONS (from part 1)
# ---------------------
def transcribe_audio(audio_path, transcript_output_path, local=False):
    """Transcribes audio using OpenAI Whisper (API or local), saves VTT."""
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found for transcription: {audio_path}")

    segments = None
    detected_language = None

    if local:
        try:
            try:
                import whisper
            except ImportError:
                print("Error: 'openai-whisper' library not installed. Cannot perform local transcription.")
                print("Install it via pip: pip install -U openai-whisper")
                return None, None

            print("Loading local Whisper model (using 'base', consider size vs performance)...")
            model = whisper.load_model("base") # Model size can be configurable
            print("Starting local transcription...")
            result = model.transcribe(audio_path, word_timestamps=True, verbose=False)
            print("Local transcription finished.")

            detected_language = result.get("language", "unknown")
            segments = result.get("segments", [])

            if not segments:
                print("Warning: Local Whisper transcription returned no segments.")
                return [], detected_language

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
            return None, None
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
                 return None, None

            print(f"Starting OpenAI API transcription for {os.path.basename(audio_path)}...")
            with open(audio_path, "rb") as audio_file:
                files["file"] = (os.path.basename(audio_path), audio_file)
                response = requests.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers=headers, files=files, data=data, timeout=600
                )
            print(f"OpenAI API response status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                detected_language = result.get("language", "unknown").lower()
                segments = result.get("segments", [])

                if not segments:
                     print("Warning: OpenAI API transcription returned no segments.")
                     safe_delete(transcript_output_path)
                     return [], detected_language

                vtt_lines = ["WEBVTT", ""]
                for segment in segments:
                    start_sec = segment.get("start")
                    end_sec = segment.get("end")
                    text = segment.get("text", "").strip()
                    if start_sec is not None and end_sec is not None and text:
                        start_time = format_vtt_timestamp(start_sec)
                        end_time = format_vtt_timestamp(end_sec)
                        vtt_lines.extend([f"{start_time} --> {end_time}", text, ""])
                    else:
                        print(f"Warning: Skipping segment with missing timestamp or text: {segment}")

                if len(vtt_lines) <= 2:
                    print("Warning: No valid segments with timestamps found after processing.")
                    safe_delete(transcript_output_path)
                    return [], detected_language

                with open(transcript_output_path, "w", encoding="utf-8") as file:
                    file.write("\n".join(vtt_lines))
                print(f"API transcription saved to: {transcript_output_path}")

            else:
                error_details = response.text
                print(f"OpenAI API Error: {response.status_code} - {error_details}")
                safe_delete(transcript_output_path)
                return None, None

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
            return None, None

    return segments, detected_language

# ---------------------
# TRANSLATION FUNCTIONS (from part 1)
# ---------------------
def translate_vtt_segments(segments, target_lang, base_vtt_filename, output_dir=TRANSCRIPTS_DIR):
    """Translates VTT segments using Google Translate and saves a new VTT file."""
    if not google_client:
        print("Error: Google Translate client not available. Skipping translation.")
        return None

    if not segments:
        print("Warning: No segments provided for translation. Skipping.")
        return None

    texts_to_translate = [segment["text"].strip() for segment in segments if segment.get("text", "").strip()]

    if not texts_to_translate:
        print("Warning: No actual text found in segments to translate.")
        return None

    translated_texts = []
    try:
        print(f"Attempting translation of {len(texts_to_translate)} non-empty segments to '{target_lang}'...")
        results = google_client.translate(texts_to_translate, target_language=target_lang)
        translated_texts = [result['translatedText'] for result in results]
        print("Translation successful.")
    except Exception as e:
        print(f"Error during Google Translate API call: {e}")
        return None

    if len(translated_texts) != len(texts_to_translate):
         print(f"Warning: Mismatch in count between non-empty original segments ({len(texts_to_translate)}) and translated texts ({len(translated_texts)}). This might indicate partial failure.")


    translated_vtt_filename = f"{base_vtt_filename}_transcription_{target_lang}.vtt"
    translated_vtt_path = os.path.join(output_dir, translated_vtt_filename)

    vtt_lines = ["WEBVTT", ""]
    translation_idx = 0
    for segment in segments:
        start_sec = segment.get("start")
        end_sec = segment.get("end")
        original_text = segment.get("text", "").strip()

        if start_sec is None or end_sec is None:
            continue

        start_time = format_vtt_timestamp(start_sec)
        end_time = format_vtt_timestamp(end_sec)

        if original_text:
            if translation_idx < len(translated_texts):
                translated_text = translated_texts[translation_idx]
                vtt_lines.extend([f"{start_time} --> {end_time}", translated_text, ""])
                translation_idx += 1
            else:
                print(f"Warning: Missing translation for segment (originally '{original_text[:30]}...'): {start_time} --> {end_time}")
                vtt_lines.extend([f"{start_time} --> {end_time}", "[Translation Failed]", ""])
        else:
             vtt_lines.extend([f"{start_time} --> {end_time}", "", ""])


    if len(vtt_lines) <= 2:
        print(f"Warning: No valid translated segments generated for {target_lang}. Skipping file write.")
        return None

    try:
        with open(translated_vtt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(vtt_lines))
        print(f"Generated translation VTT: {translated_vtt_path}")
        return translated_vtt_path
    except IOError as e:
        print(f"Error writing translated VTT file {translated_vtt_path}: {e}")
        return None


# ------------------------------------------------------------
# HELPER FOR METADATA: Extract Text from VTT String (from part 2)
# ------------------------------------------------------------
def extract_text_from_vtt_string(vtt_content_string):
    """Reads VTT content string and extracts only the spoken text blocks."""
    if not vtt_content_string or not isinstance(vtt_content_string, str):
        return ""
    lines = vtt_content_string.strip().splitlines()
    text_content = []
    potential_text_line = False
    for line in lines:
        line = line.strip()
        if line == "" or line.startswith("WEBVTT") or line.startswith("NOTE") or line.startswith("STYLE"):
            potential_text_line = False
            continue
        if re.match(r'^\d{2}:\d{2}:\d{2}\.\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}\.\d{3}', line):
            potential_text_line = True
            continue
        if potential_text_line:
            if not re.match(r'^\d{2}:\d{2}:\d{2}\.\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}\.\d{3}', line):
                 text_content.append(line)
            else:
                 potential_text_line = False

    return " ".join(text_content)

# ------------------------------------------------------------
# HELPER FOR METADATA: Keyword Extraction (from part 2)
# ------------------------------------------------------------
def extract_keywords_from_text(text, num_keywords=10):
    """Extracts simple keywords based on word frequency."""
    if not text: return []
    try:
        stopwords = set([
            "the", "and", "a", "to", "of", "in", "that", "is", "it", "for", "on", "with", "as", "by", "at", "an",
            "this", "or", "be", "are", "was", "were", "i", "you", "he", "she", "we", "they", "my", "your", "his",
            "her", "its", "our", "their", "from", "up", "out", "if", "about", "into", "not", "have", "has", "had",
            "do", "does", "did", "will", "would", "shall", "should", "can", "could", "may", "might", "must", "also",
            "but", "so", "just", "like", "get", "go", "make", "know", "see", "say", "think", "time", "use", "work",
            " K", " G", " M", " T", " s", " m", " pm", " am",
            "को", "मा", "छ", "र", "हरु", "यो", "त्यो", "ने", "लागि", "पनि", "एक", "छन्", "गरी", "हो", "के", "छैन",
            "ले", "लाई", "बाट", "त", "भने", "अब", "कि", "संग", "अनि", "गर्नु", "भएको", "भए", "गरेको", "हुन्छ", "तर",
            "यी", "ती", "नै", "जब", "तब", "यहाँ", "त्यहाँ", "कसरी", "किन", "धेरै", "थोरै", "राम्रो", "नराम्रो"
        ])
        words = re.findall(r'\b\w+\b', text.lower())
        filtered_words = [w for w in words if w not in stopwords and len(w) > 2 and not w.isdigit()]
        if not filtered_words: return []
        word_freq = Counter(filtered_words)
        common_keywords = [word for word, freq in word_freq.most_common(num_keywords)]
        return common_keywords
    except Exception as e:
         print(f"Error during keyword extraction: {e}")
         return []


# ------------------------------------------------------------
# --- Integrated Metadata Generation Function (from part 2) ---
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
        return

    transcript_content_map = doc_data.get("transcript_content", {})
    selected_vtt_content = None
    selected_lang = None

    if not transcript_content_map:
         print(f"Warning: No transcript content available in doc_data for job_id '{job_id}'. Skipping metadata generation.")
         return

    detected_lang = doc_data.get("detected_language")
    preferred_langs_order = [detected_lang, 'en', 'ne']

    for lang in preferred_langs_order:
        if lang and lang in transcript_content_map:
            selected_lang = lang
            selected_vtt_content = transcript_content_map[lang]
            if isinstance(selected_vtt_content, str) and selected_vtt_content.startswith("Error: Could not read file"):
                print(f"Warning: Content for preferred language '{selected_lang}' is an error message. Trying next.")
                selected_vtt_content = None
                selected_lang = None
            else:
                break

    if not selected_lang and transcript_content_map:
        for lang, content in transcript_content_map.items():
             if isinstance(content, str) and not content.startswith("Error: Could not read file"):
                 selected_lang = lang
                 selected_vtt_content = content
                 print(f"Warning: Using first available valid language '{selected_lang}' for keyword extraction.")
                 break

    if not selected_lang or not selected_vtt_content:
        print("Could not select any valid transcript content for keyword extraction. Skipping.")
        doc_data['keywords'] = doc_data.get('keywords', [])
        return

    print(f"Selected language '{selected_lang}' for keyword extraction.")

    vtt_text_for_keywords = extract_text_from_vtt_string(selected_vtt_content)
    if not vtt_text_for_keywords:
        print("Warning: Could not extract plain text from selected VTT content. Skipping keyword extraction.")
        doc_data['keywords'] = doc_data.get('keywords', [])
        return

    keywords = extract_keywords_from_text(vtt_text_for_keywords)
    print(f"Extracted keywords ({len(keywords)}): {keywords}")

    doc_data['keywords'] = keywords

    if not doc_data.get('title') and vtt_text_for_keywords:
        first_sentence_match = re.match(r"^.*?[.?!]", vtt_text_for_keywords)
        if first_sentence_match:
            potential_title = first_sentence_match.group(0).strip()
            if len(potential_title) > 10 and len(potential_title) < 100 :
                doc_data['title'] = potential_title
                print(f"Inferred title: {potential_title}")

    if not doc_data.get('summary') and vtt_text_for_keywords:
         words = vtt_text_for_keywords.split()
         potential_summary = " ".join(words[:50]) + ("..." if len(words) > 50 else "")
         doc_data['summary'] = potential_summary
         print(f"Generated simple summary (first 50 words).")

    if not doc_data.get('location') and vtt_text_for_keywords:
        # Look for patterns like "in Kathmandu", "at Swayambhu" etc.
        loc_match = re.search(r'\b(?:in|at|near)\s+([A-Z][A-Za-z\s\-]+)\b', vtt_text_for_keywords)
        if loc_match:
            doc_data['location'] = f"Possibly: {loc_match.group(1).strip()}"
            print(f"Inferred location: {doc_data['location']}")

    if not doc_data.get('speaker') and vtt_text_for_keywords:
         # Look for patterns like "Speaker: John Doe", "by Jane Smith"
        sp_match = re.search(r'\b(?:by|from|speaker[:]?|voiced by)\s+([A-Z][A-Za-z\s\.\-]+)\b', vtt_text_for_keywords)
        if sp_match:
            doc_data['speaker'] = f"Possibly: {sp_match.group(1).strip()}"
            print(f"Inferred speaker: {doc_data['speaker']}")

    print(f"--- Finished automatic metadata generation for job: {job_id} ---")


# ------------------------------------------------------------
# --- MAIN PROCESSING ENDPOINT (Storing VTT Content) (from part 2) ---
# ------------------------------------------------------------
@app.route("/api/generate-transcription", methods=["POST", "OPTIONS"])
def generate_transcription_endpoint():
    """
    Handles media processing, transcription, translation,
    and stores VTT *content* in the database. Deletes local VTT files afterwards.
    Optionally generates and adds further metadata based on a request parameter.
    """
    if request.method == "OPTIONS":
        response = jsonify({"message": "Preflight OK"})
        return response, 200

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
    doc_data = {}

    try:
        timestamp = get_timestamp()

        if request.is_json:
            data = request.json
            if not data:
                 return jsonify({"status": "error", "message": "Received JSON content type but empty request body"}), 400

            source_type = data.get("source_type", "").lower()
            source = data.get("source", "")

            raw_gen_meta = data.get("generate_metadata", False)
            should_generate_metadata = str(raw_gen_meta).lower() == 'true' if isinstance(raw_gen_meta, str) else bool(raw_gen_meta)
            raw_local = data.get("local_transcription", False)
            use_local_whisper = str(raw_local).lower() == 'true' if isinstance(raw_local, str) else bool(raw_local)

            if not source_type or not source:
                 return jsonify({"status": "error", "message": "Missing 'source_type' or 'source' in JSON body"}), 400
            if source_type not in ["youtube", "mp4"]:
                 return jsonify({"status": "error", "message": f"Invalid 'source_type' '{source_type}'. Must be 'youtube' or 'mp4'."}), 400

            original_media_name = source

        elif request.files:
            source_type = request.form.get("source_type", "").lower()
            source_input = request.files.get("source")

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
            "category": None,
            "keywords": [],
            "title": None,
            "summary": None,
            "last_updated": None,
        }
        if content_read_errors:
             doc_data["processing_info"]["content_read_errors"] = content_read_errors

        # --- 6. CONDITIONAL: Generate Additional Metadata ---
        if should_generate_metadata:
            print(f"Flag 'generate_metadata' is True. Calling metadata generation function for job: {vtt_base_filename}")
            try:
                generate_and_populate_metadata(doc_data) # Modifies doc_data in place
            except Exception as e:
                print(f"Error during metadata generation step: {e}")
                traceback.print_exc()
                doc_data["processing_info"]["metadata_generation_error"] = str(e)
        else:
             print(f"Flag 'generate_metadata' is False. Skipping automatic metadata generation.")

        # --- 7. Insert or Update in DB ---
        existing = collection.find_one({"job_id": vtt_base_filename})
        current_iso_time = dt.now() # Keep as datetime object until final conversion for DB/JSON
        # Use dt.now().isoformat() only for JSON output, keep datetime objects for DB
        doc_data["last_updated"] = current_iso_time # Set last updated time as datetime object

        if existing:
            print(f"Updating DB entry for job_id: {vtt_base_filename}")
            update_payload = doc_data.copy()
            if "date_added" in update_payload:
                 del update_payload["date_added"]

            update_result = collection.update_one(
                 {"_id": existing["_id"]},
                 {"$set": update_payload}
             )
            db_status = "updated" if update_result.modified_count > 0 else "no change"
            inserted_id = str(existing["_id"])

        else:
            print(f"Creating new DB entry for job_id: {vtt_base_filename}")
            doc_data["date_added"] = current_iso_time # Set date_added as datetime object
            insert_result = collection.insert_one(doc_data)
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
        # Convert datetime objects to ISO strings for the final JSON response
        response_data = {
            "status": db_status,
            "job_id": vtt_base_filename,
            "detected_language": standardized_lang,
            "message": f"Processing complete for {original_media_name}. Status: {db_status}.",
            "inserted_or_updated_id": inserted_id,
            # Shorten content preview for response
            "transcript_en_preview": db_transcript_content.get('en', '')[:100] + "..." if isinstance(db_transcript_content.get('en'), str) and db_transcript_content.get('en') else "N/A",
            "transcript_ne_preview": db_transcript_content.get('ne', '')[:100] + "..." if isinstance(db_transcript_content.get('ne'), str) and db_transcript_content.get('ne') else "N/A",
            "filename": original_media_name,
            "date_added": doc_data.get('date_added').isoformat() if isinstance(doc_data.get('date_added'), datetime.datetime) else doc_data.get('date_added'),
            "last_updated": doc_data.get('last_updated').isoformat() if isinstance(doc_data.get('last_updated'), datetime.datetime) else doc_data.get('last_updated'),
            "title": doc_data.get("title"),
            "speaker": doc_data.get("speaker"),
            "location": doc_data.get("location"),
            "category": doc_data.get("category"),
            "keywords": doc_data.get("keywords"),
            "summary": doc_data.get("summary")
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
        traceback.print_exc() # Log traceback for runtime errors
        for path in files_to_clean: safe_delete(path)
        return jsonify({"status": "error", "message": f"Processing error: {e}"}), 500
    except Exception as e:
        print(f"Error - Unexpected Internal Server Error: {e}")
        traceback.print_exc() # Log full traceback for unexpected errors
        for path in files_to_clean: safe_delete(path)
        return jsonify({"status": "error", "message": f"An unexpected internal server error occurred: {e}"}), 500


# ------------------------------------------------------------
# --- Comment out the old separate metadata endpoint (from part 2) ---
# --- This can be repurposed for MANUAL updates later if needed ---
# ------------------------------------------------------------
# @app.route("/api/generate-metadata", methods=["POST", "OPTIONS"])
# def generate_metadata_endpoint_old():
#    ... (commented out function body) ...


# --- Main Execution ---
if __name__ == "__main__":
    print(f"Starting Flask server at {dt.now().isoformat()}...")
    print(f"Audio Directory: {os.path.abspath(AUDIO_DIR)}")
    print(f"Transcripts Directory: {os.path.abspath(TRANSCRIPTS_DIR)}")
    print(f"Google Translate Client Available: {'Yes' if google_client else 'No'}")
    print(f"OpenAI API Key Set: {'Yes' if OPENAI_API_KEY else 'No'}")
    # Set debug=True for development. Set host='0.0.0.0' to make it accessible externally (use with caution).
    app.run(host="0.0.0.0", port=5000, debug=True)