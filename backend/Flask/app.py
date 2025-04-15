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

app = Flask(__name__)
# Allow all origins for all /api/* routes.
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# ------------------------------------------------------
# Set up Google Translate credentials and OpenAI API key.
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.expanduser(
    ""
)
from google.cloud import translate_v2 as translate
google_client = translate.Client()

OPENAI_API_KEY = ""
# ------------------------------------------------------

# ------------------------------------------------------
# Connect to MongoDB using pymongo:
client = MongoClient("mongodb://localhost:27017/")
db = client["swayambhu"]
collection = db["transcripts"]
# ------------------------------------------------------

# ---------------------
# Helper Functions
# ---------------------
def get_timestamp():
    """Generate a unique timestamp string."""
    return dt.now().strftime("%Y%m%d_%H%M%S")

def format_vtt_timestamp(seconds):
    """Convert seconds to VTT timestamp format (HH:MM:SS.mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}.{millisecs:03}"

def adjust_filepath(filepath):
    """Remove 'backend/' prefix if present."""
    if filepath.startswith("backend/"):
        return filepath[len("backend/"):]
    return filepath

# <<-- Added extract_youtube_title function (minimal changes) -->> 
def extract_youtube_title(youtube_url):
    """Use yt_dlp to extract the video title and clean it as a filename."""
    try:
        import yt_dlp as youtube_dl
        ydl_opts = {"quiet": True}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
        title = info.get("title", "unknown_title")
        # Clean filename: remove spaces and non-alphanumeric characters.
        title_clean = re.sub(r'\W+', '_', title).strip("_").lower()
        return title_clean
    except Exception as e:
        print(f"Error extracting title: {e}")
        return "unknown_title"

# ---------------------
# MEDIA PROCESSING FUNCTIONS
# ---------------------
def extract_audio_from_video(input_path):
    """Extract audio from a video file (MOV/MP4) and save as MP3."""
    output_audio_path = os.path.splitext(input_path)[0] + ".mp3"
    command = [
        "ffmpeg",
        "-i", input_path,
        "-vn",
        "-acodec", "mp3",
        "-ar", "44100",
        "-ac", "2",
        output_audio_path
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_audio_path

def download_audio(youtube_url):
    """Download audio from a YouTube URL and convert it to MP3."""
    output_path = os.path.join("audio_files", "audio.mp3")  # Output file path
    import yt_dlp as youtube_dl
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join("audio_files", "audio"),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    print("Downloading YouTube audio as MP3...")
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])
    print(f"Audio saved as: {output_path}")
    return output_path

# ---------------------
# TRANSCRIPTION FUNCTIONS
# ---------------------
def transcribe_audio(audio_path, transcript_path, language_code=None, local=False):
    """
    Transcribe audio and generate a VTT file.
    When local is True, run local Whisper; otherwise, use the Whisper API.
    """
    if local:
        try:
            import whisper
            print(f"Transcribing (local) {audio_path} ...")
            model = whisper.load_model("large")
            result = model.transcribe(audio_path, word_timestamps=True, verbose=True)
            detected_language = result.get("language", "unknown")
            print(f"Detected language: {detected_language}")
            segments = result["segments"]
            vtt_lines = ["WEBVTT", ""]
            for segment in segments:
                start_time = format_vtt_timestamp(segment["start"])
                end_time = format_vtt_timestamp(segment["end"])
                text = segment["text"].strip()
                vtt_lines.append(f"{start_time} --> {end_time}")
                vtt_lines.append(text)
                vtt_lines.append("")
            with open(transcript_path, "w", encoding="utf-8") as file:
                file.write("\n".join(vtt_lines))
            print(f"Saved VTT transcription to {transcript_path}")
            return segments, detected_language
        except Exception as e:
            print(f"Error during local transcription: {e}")
            return None, None
    else:
        print(f"Transcribing via API {audio_path} ...")
        url_api = "https://api.openai.com/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        data = {
            "model": "whisper-1",
            "response_format": "verbose_json",
            "timestamp_granularities": "segment"
        }
        if language_code:
            data["language"] = language_code
        files = {"file": open(audio_path, "rb")}
        try:
            response = requests.post(url_api, headers=headers, data=data, files=files)
            files["file"].close()
            if response.status_code == 200:
                result = response.json()
                detected_language = result.get("language", "unknown")
                if "segments" not in result:
                    print("No segments found in API response.")
                    return None, None
                segments = result["segments"]
                vtt_lines = ["WEBVTT", ""]
                for segment in segments:
                    start_time = format_vtt_timestamp(segment["start"])
                    end_time = format_vtt_timestamp(segment["end"])
                    text = segment["text"].strip()
                    vtt_lines.append(f"{start_time} --> {end_time}")
                    vtt_lines.append(text)
                    vtt_lines.append("")
                with open(transcript_path, "w", encoding="utf-8") as file:
                    file.write("\n".join(vtt_lines))
                print(f"Saved VTT transcription to {transcript_path}")
                return segments, detected_language
            else:
                print(f"Error: {response.status_code} response: {response.text}")
                return None, None
        except Exception as e:
            print(f"Exception during API transcription: {e}")
            return None, None

# ---------------------
# TRANSLATION FUNCTIONS
# ---------------------
def translate_text_google(text_list, target_language="en"):
    if isinstance(text_list, list):
        result = google_client.translate(text_list, target_language=target_language)
        return [res['translatedText'] for res in result]
    else:
        result = google_client.translate(text_list, target_language=target_language)
        return result['translatedText']

def translate_vtt(segments, source_lang, target_lang="en", audio_file=None):
    """Translate segments (assumed to have keys 'start', 'end', 'text') and write a VTT file."""
    texts = [segment["text"].strip() for segment in segments]
    translated_texts = translate_text_google(texts, target_lang)
    translated_vtt_path = os.path.join(
        "transcripts",
        f"{os.path.splitext(os.path.basename(audio_file))[0]}_{get_timestamp()}_transcription_{target_lang}.vtt"
    )
    vtt_lines = ["WEBVTT", ""]
    for idx, segment in enumerate(segments):
        start_time = segment["start"] if isinstance(segment["start"], str) else format_vtt_timestamp(segment["start"])
        end_time = segment["end"] if isinstance(segment["end"], str) else format_vtt_timestamp(segment["end"])
        vtt_lines.append(f"{start_time} --> {end_time}")
        vtt_lines.append(translated_texts[idx])
        vtt_lines.append("")
    with open(translated_vtt_path, "w", encoding="utf-8") as file:
        file.write("\n".join(vtt_lines))
    print(f"Translated VTT saved to: {translated_vtt_path}")

# ---------------------
# SUBTITLE PARSING FUNCTIONS
# ---------------------
def parse_vtt(vtt_file_path):
    """Parse a VTT file and return segments as a list of dictionaries."""
    segments = []
    try:
        with open(vtt_file_path, "r", encoding="utf-8") as file:
            content = file.read().strip()
        if content.startswith("WEBVTT"):
            content = content.split("\n", 1)[1].strip()
        blocks = content.split("\n\n")
        for block in blocks:
            lines = block.split("\n")
            if len(lines) >= 2 and " --> " in lines[0]:
                start_time, end_time = lines[0].split(" --> ")
                text = " ".join(lines[1:]).strip()
                segments.append({"start": start_time, "end": end_time, "text": text})
    except Exception as e:
        print(f"Error parsing VTT file: {e}")
        return None
    return segments

# ---------------------
# CLEANUP FUNCTION
# ---------------------
def cleanup_file(file_path):
    """Delete a temporary file if it exists."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Cleaned up temporary file: {file_path}")
    except Exception as e:
        print(f"Error cleaning up file {file_path}: {e}")

# ---------------------
# ENDPOINTS
# ----------------------

# Endpoint: Generate Transcription
# Supports only YouTube URLs and MP4 files (drag and drop)
@app.route("/api/generate-transcription", methods=["POST", "OPTIONS"])
def generate_transcription_endpoint():
    if request.method == "OPTIONS":
        return jsonify({"message": "Preflight OK"}), 200

    data = request.json
    source_type = data.get("source_type", "").lower()
    source = data.get("source", "")
    if not source_type or not source:
        return jsonify({"error": "Both 'source_type' and 'source' are required."}), 400

    filename = ""
    db_url = ""
    if source_type == "youtube":
        filename = extract_youtube_title(source)
        db_url = source  # Save the YouTube URL in the DB.
        # Download audio from YouTube.
        processed_audio = download_audio(source)
    elif source_type == "mp4":
        if not os.path.exists(source):
            return jsonify({"error": "The specified MP4 file does not exist."}), 404
        filename = os.path.splitext(os.path.basename(source))[0]
        processed_audio = extract_audio_from_video(source)
    else:
        return jsonify({"error": "source_type must be either 'youtube' or 'mp4'."}), 400

    # Determine transcript path for English transcript.
    transcript_path = os.path.join("transcripts", f"original_{filename}_{get_timestamp()}_transcription_en.vtt")
    # Transcribe using API-based transcription.
    segments, detected_lang = transcribe_audio(processed_audio, transcript_path, language_code="en", local=False)
    if segments is None or detected_lang is None:
        return jsonify({"error": "English transcription failed."}), 500

    # Read the generated English transcript.
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript_en_text = f.read()
    except Exception as e:
        return jsonify({"error": f"Error reading English transcript: {str(e)}"}), 500

    # Generate Nepali transcript via translation.
    # Here we use the same segments from transcription.
    translate_vtt(segments, detected_lang, target_lang="ne", audio_file=processed_audio)
    # Locate the Nepali transcript by globbing the transcripts folder.
    ne_pattern = os.path.join("transcripts", f"{filename}_*_transcription_ne.vtt")
    ne_files = glob.glob(ne_pattern)
    if ne_files:
        nepali_file = max(ne_files, key=os.path.getmtime)
        with open(nepali_file, "r", encoding="utf-8") as f:
            transcript_ne_text = f.read()
    else:
        transcript_ne_text = ""

    # Update (or create) the document in MongoDB.
    doc = collection.find_one({"filename": filename})
    if doc:
        update_fields = {
            "transcript_en": transcript_en_text,
            "transcript_ne": transcript_ne_text,
        }
        if db_url:
            update_fields["url"] = db_url
        collection.update_one({"_id": doc["_id"]}, {"$set": update_fields})
        status_msg = "updated"
    else:
        new_doc = {
            "filename": filename,
            "date_added": dt.now().isoformat(),
            "date_recorded": "",
            "language": "en",
            "transcript_en": transcript_en_text,
            "transcript_ne": transcript_ne_text,
            "url": db_url,
            "location": "",
            "speaker": "",
            "type": "",
            "keywords": []
        }
        collection.insert_one(new_doc)
        status_msg = "created"

    # Cleanup temporary processed audio file.
    cleanup_file(processed_audio)

    return jsonify({
        "status": status_msg,
        "filename": filename,
        "transcript_en": transcript_en_text,
        "transcript_ne": transcript_ne_text
    })

# Endpoint: Generate Metadata from a VTT File
@app.route("/api/generate-metadata", methods=["POST", "OPTIONS"])
def generate_metadata():
    if request.method == "OPTIONS":
        return jsonify({"message": "Preflight OK"}), 200

    data = request.json
    vtt_filename = data.get("vtt_filename", "")
    if not vtt_filename:
        return jsonify({"error": "vtt_filename is required"}), 400
    if not os.path.exists(vtt_filename):
        return jsonify({"error": "The specified VTT file does not exist"}), 404

    # Extract base filename assuming naming pattern like my_dog_123_*_transcription_en.vtt.
    pattern = r'^(.*?)_.*_transcription_(\w+)\.vtt$'
    m = re.match(pattern, os.path.basename(vtt_filename))
    if m:
        base_filename = m.group(1)
    else:
        base_filename = os.path.splitext(os.path.basename(vtt_filename))[0]

    doc = collection.find_one({"filename": base_filename})
    if not doc:
        return jsonify({"error": "No entry found for the given filename. Generate transcription first."}), 404

    try:
        with open(vtt_filename, "r", encoding="utf-8") as f:
            transcript_text = f.read()
    except Exception as e:
        return jsonify({"error": f"Error reading VTT file: {str(e)}"}), 500

    url_field = data.get("url", "")
    location = data.get("location", "")
    speaker = data.get("speaker", "")
    videotype = data.get("type", "")

    if not location:
        loc_match = re.search(r'\bin\s+([A-Za-z]+)\b', transcript_text)
        if loc_match:
            location = f"possibly: {loc_match.group(1)}"
    if not speaker:
        sp_match = re.search(r'\bby\s+([A-Za-z ]+)\b', transcript_text)
        if sp_match:
            speaker = f"possibly: {sp_match.group(1).strip()}"

    def extract_keywords(text):
        from collections import Counter
        stopwords = set(["the", "and", "a", "to", "of", "in", "that", "is", "it", "for", "on", "with", "as", "by", "at"])
        words = re.findall(r'\w+', text.lower())
        filtered = [w for w in words if w not in stopwords and len(w) > 3]
        freq = Counter(filtered)
        common = freq.most_common(5)
        return [w for w, count in common]
    keywords = extract_keywords(transcript_text)

    updates = {
        "language": doc.get("language", "unknown"),
        "transcript_en": transcript_text,
        "url": url_field,
        "location": location,
        "speaker": speaker,
        "type": videotype,
        "keywords": keywords,
    }
    if "date_added" not in doc or not doc["date_added"]:
        updates["date_added"] = dt.now().isoformat()

    collection.update_one({"_id": doc["_id"]}, {"$set": updates})
    return jsonify({
        "status": "metadata updated",
        "filename": base_filename,
        "keywords": keywords
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
