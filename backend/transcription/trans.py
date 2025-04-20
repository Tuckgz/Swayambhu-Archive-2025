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

# Set up Google Translate credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.expanduser(
    "/Users/tuckr/APIs/Google Cloud/swayambhu-451702-e759a9ee59ab.json"
)
google_client = translate.Client()

# Your OpenAI API key (replace as needed)
openai_key = os.getenv("OPENAI_API_KEY")

# Ensure required directories exist
os.makedirs("audio_files", exist_ok=True)
os.makedirs("transcripts", exist_ok=True)

# ---------------------
# HELPER FUNCTIONS
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
    if filepath.startswith("backend/"):
        return filepath[len("backend/"):]
    return filepath

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
    output_path = os.path.join("audio_files", "audio.mp3")
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
                vtt_lines.extend([f"{start_time} --> {end_time}", text, ""])
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write("\n".join(vtt_lines))
            print(f"Saved VTT transcription to {transcript_path}")
            return segments, detected_language

        except Exception as e:
            print(f"Error during local transcription: {e}")
            return None, None

    else:
        print(f"Transcribing via API {audio_path} ...")
        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {openai_key}"}
        data = {
            "model": "whisper-1",
            "response_format": "verbose_json",
            "timestamp_granularities": "segment"
        }
        if language_code:
            data["language"] = language_code
        files = {"file": open(audio_path, "rb")}
        try:
            response = requests.post(url, headers=headers, data=data, files=files)
            files["file"].close()
            if response.status_code != 200:
                print(f"Error: {response.status_code} response: {response.text}")
                return None, None

            result = response.json()
            detected_language = result.get("language", "unknown")
            segments = result.get("segments", [])
            if not segments:
                print("No segments found in API response.")
                return None, None

            vtt_lines = ["WEBVTT", ""]
            for segment in segments:
                start_time = format_vtt_timestamp(segment["start"])
                end_time = format_vtt_timestamp(segment["end"])
                text = segment["text"].strip()
                vtt_lines.extend([f"{start_time} --> {end_time}", text, ""])
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write("\n".join(vtt_lines))
            print(f"Saved VTT transcription to {transcript_path}")
            return segments, detected_language

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
    """Translate segments and write a VTT file."""
    texts = [seg["text"].strip() for seg in segments]
    translated_texts = translate_text_google(texts, target_language=target_lang)
    translated_vtt_path = os.path.join(
        "transcripts",
        f"{os.path.splitext(os.path.basename(audio_file))[0]}_{get_timestamp()}_{target_lang}.vtt"
    )
    vtt_lines = ["WEBVTT", ""]
    for idx, seg in enumerate(segments):
        start = seg["start"] if isinstance(seg["start"], str) else format_vtt_timestamp(seg["start"])
        end   = seg["end"]   if isinstance(seg["end"], str)   else format_vtt_timestamp(seg["end"])
        vtt_lines.extend([f"{start} --> {end}", translated_texts[idx], ""])
    with open(translated_vtt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(vtt_lines))
    print(f"Translated VTT saved to: {translated_vtt_path}")

# ---------------------
# SUBTITLE PARSING FUNCTIONS
# ---------------------
def parse_vtt(vtt_file_path):
    """Parse a VTT file and return segments as a list of dicts."""
    segments = []
    try:
        with open(vtt_file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content.startswith("WEBVTT"):
            content = content.split("\n", 1)[1].strip()
        blocks = content.split("\n\n")
        for block in blocks:
            lines = block.split("\n")
            if len(lines) >= 2 and " --> " in lines[0]:
                start, end = lines[0].split(" --> ")
                text = " ".join(lines[1:]).strip()
                segments.append({"start": start, "end": end, "text": text})
    except Exception as e:
        print(f"Error parsing VTT file: {e}")
        return None
    return segments

def process_subtitle(vtt_file, translate_flag):
    """Process a VTT subtitle file for translation only."""
    segments = parse_vtt(vtt_file)
    if translate_flag and segments:
        translate_vtt(segments, source_lang="unknown", target_lang="en", audio_file=vtt_file)
    else:
        print("Skipping translation for subtitle file.")

# ---------------------
# PROCESSING FUNCTION
# ---------------------
def process_audio(
    audio_method,          # 0=video file,1=YouTube,2=MP3,3=VTT-only
    audio_url=None,
    audio_file=None,
    mp3_file=None,
    vtt_file=None,
    transcribe_flag=1,
    transcription_method=1,  # 1=API,2=Local,3=API-forced
    translate_flag=0,
    forced_lang=None
):
    if audio_file:
        audio_file = adjust_filepath(audio_file)
    if mp3_file:
        mp3_file = adjust_filepath(mp3_file)
    if vtt_file:
        vtt_file = adjust_filepath(vtt_file)

    # Step 1: get the audio
    if audio_method == 0:
        if not audio_file:
            raise ValueError("A video file path is required for video processing.")
        processed_audio = extract_audio_from_video(audio_file)
    elif audio_method == 1:
        if not audio_url:
            raise ValueError("A YouTube URL is required for audio URL processing.")
        processed_audio = download_audio(audio_url)
    elif audio_method == 2:
        if not mp3_file:
            raise ValueError("An MP3 file path is required.")
        processed_audio = mp3_file
    elif audio_method == 3:
        if not vtt_file:
            raise ValueError("A VTT subtitle file path is required.")
        process_subtitle(vtt_file, translate_flag=1)
        return
    else:
        raise ValueError("Invalid audio_method value.")

    # Step 2: transcription
    segments = None
    detected_lang = None
    if transcribe_flag == 1:
        base_name = os.path.splitext(os.path.basename(processed_audio))[0]
        transcript_path = os.path.join("transcripts", f"original_{base_name}.vtt")

        if transcription_method == 1:
            segments, detected_lang = transcribe_audio(processed_audio, transcript_path)
        elif transcription_method == 2:
            try:
                from backend.transcription.development.local_transcribe import local_whisper
                segments, detected_lang = local_whisper(processed_audio, transcript_path)
            except ImportError:
                print("local_whisper not found.")
                return
        elif transcription_method == 3:
            if forced_lang is None:
                raise ValueError("Forced language code must be provided for transcription_method 3.")
            segments, detected_lang = transcribe_audio(processed_audio, transcript_path, language_code=forced_lang)
        else:
            raise ValueError("Invalid transcription_method.")

        if segments is None or detected_lang is None:
            print("Error: Transcription failed.")
            return

        # —— RENAME to include detected language ——
        lang = detected_lang if isinstance(detected_lang, str) else "unknown"
        new_name = f"original_{base_name}_{lang}.vtt"
        new_path = os.path.join("transcripts", new_name)
        try:
            os.rename(transcript_path, new_path)
            transcript_path = new_path
            print(f"Renamed transcript to: {new_name}")
        except Exception as e:
            print(f"Warning: could not rename transcript file: {e}")

    elif transcribe_flag == 0:
        if audio_method != 3:
            raise ValueError("Transcription skipped but input is not a subtitle file.")
    else:
        raise ValueError("Invalid transcribe_flag value.")

    # Step 3: translation
    if translate_flag and segments and detected_lang:
        translate_vtt(segments, detected_lang, target_lang="en", audio_file=processed_audio)
    else:
        print("Skipping translation.")

# ---------------------
# COMMAND-LINE INTERFACE
# ---------------------
def main():
    parser = argparse.ArgumentParser(
        description="Tool to process video/audio/subtitle files for transcription and translation."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=str, help="Path to an input file (video, MP3, or VTT)")
    group.add_argument("--dir", type=str, help="Directory containing video files to process")
    group.add_argument("--youtube", type=str, help="YouTube or audio URL to download and process")

    parser.add_argument("--vtt", action="store_true", help="Input file is a VTT subtitle file (translation only)")
    parser.add_argument("--mp3", action="store_true", help="Input file is an MP3 file")
    parser.add_argument("--local", "-l", action="store_true", help="Run local Whisper transcription")
    parser.add_argument("--translate", "-t", action="store_true", help="Also translate to English")
    parser.add_argument("--lang", type=str, help="Forced language code for transcription")

    args = parser.parse_args()

    # Decide transcription method
    if args.lang:
        transcription_method = 3
        forced_lang = args.lang
    else:
        transcription_method = 2 if args.local else 1
        forced_lang = None

    if args.youtube:
        process_audio(
            audio_method=1,
            audio_url=args.youtube,
            transcribe_flag=1,
            transcription_method=transcription_method,
            translate_flag=args.translate,
            forced_lang=forced_lang
        )
    elif args.vtt:
        process_audio(
            audio_method=3,
            vtt_file=args.file,
            transcribe_flag=0,
            translate_flag=1
        )
    elif args.mp3:
        process_audio(
            audio_method=2,
            mp3_file=args.file,
            transcribe_flag=1,
            transcription_method=transcription_method,
            translate_flag=args.translate,
            forced_lang=forced_lang
        )
    elif args.dir:
        video_extensions = ("*.mp4", "*.mov")
        files = []
        for ext in video_extensions:
            files.extend(glob.glob(os.path.join(args.dir, ext)))
        if not files:
            print(f"No video files found in directory: {args.dir}")
            sys.exit(1)
        for file_path in files:
            print(f"\nProcessing file: {file_path}")
            process_audio(
                audio_method=0,
                audio_file=file_path,
                transcribe_flag=1,
                transcription_method=transcription_method,
                translate_flag=args.translate,
                forced_lang=forced_lang
            )
    else:
        process_audio(
            audio_method=0,
            audio_file=args.file,
            transcribe_flag=1,
            transcription_method=transcription_method,
            translate_flag=args.translate,
            forced_lang=forced_lang
        )

if __name__ == "__main__":
    main()
