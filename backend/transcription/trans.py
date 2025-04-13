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

# Set up Google Translate credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.expanduser(
    ""
)
google_client = translate.Client()

# Your OpenAI API key (replace as needed)
OPENAI_API_KEY = ""

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
    output_path = os.path.join("audio_files", "audio.mp3")  # Output file path
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
        # Local transcription using Whisper
        try:
            import whisper  # Import locally so dependency is optional
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
        # API-based transcription using OpenAI Whisper API
        print(f"Transcribing via API {audio_path} ...")
        url = "https://api.openai.com/v1/audio/transcriptions"
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
            response = requests.post(url, headers=headers, data=data, files=files)
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

def translate_srt(segments, source_lang, target_lang="en", audio_file=None):
    """Translate segments (assumed to have keys 'start', 'end', 'text') and write a VTT file."""
    texts = [segment["text"].strip() for segment in segments]
    translated_texts = translate_text_google(texts, target_lang)
    translated_vtt_path = os.path.join(
        "transcripts",
        f"{os.path.splitext(os.path.basename(audio_file))[0]}_{get_timestamp()}_en.vtt"
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
def parse_srt(srt_file_path):
    """Parse an SRT file and return segments as a list of dictionaries."""
    segments = []
    try:
        with open(srt_file_path, "r", encoding="utf-8") as file:
            content = file.read().strip()
        # Assume SRT blocks are separated by two newlines.
        blocks = content.split("\n\n")
        for block in blocks:
            lines = block.split("\n")
            if len(lines) >= 3:
                # SRT blocks begin with an index, then time range, then text.
                try:
                    # index = int(lines[0].strip())
                    times = lines[1].strip()
                    start_time, end_time = times.split(" --> ")
                    text = " ".join(lines[2:]).strip()
                    segments.append({"start": start_time, "end": end_time, "text": text})
                except Exception:
                    continue
    except Exception as e:
        print(f"Error parsing SRT file: {e}")
        return None
    return segments

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

def process_subtitle(sub_file, translate_flag):
    """Process a subtitle file (SRT or VTT) for translation."""
    if sub_file.lower().endswith(".vtt"):
        segments = parse_vtt(sub_file)
    else:
        segments = parse_srt(sub_file)
    if translate_flag and segments:
        translate_srt(segments, source_lang="unknown", target_lang="en", audio_file=sub_file)
    else:
        print("Skipping translation for subtitle file.")

# ---------------------
# PROCESSING FUNCTION
# ---------------------
def process_audio(
    audio_method,          # 0 = MOV/MP4, 1 = YouTube URL, 2 = MP3, 3 = Subtitle file (SRT/VTT)
    audio_url=None,
    audio_file=None,
    mp3_file=None,
    srt_file=None,
    transcribe_flag=1,
    transcription_method=1,  # 1 = API, 2 = Local, 3 = API (Forced Language)
    translate_flag=0,
    forced_lang=None
):
    """
    Process the input based on the audio_method and flags.
    """
    # Adjust file paths if provided.
    if audio_file:
        audio_file = adjust_filepath(audio_file)
    if mp3_file:
        mp3_file = adjust_filepath(mp3_file)
    if srt_file:
        srt_file = adjust_filepath(srt_file)

    processed_audio = None
    # Determine input source.
    if audio_method == 0:
        # Video file
        if not audio_file:
            raise ValueError("A video file path is required for video processing.")
        processed_audio = extract_audio_from_video(audio_file)
    elif audio_method == 1:
        # YouTube URL
        if not audio_url:
            raise ValueError("A YouTube URL is required for audio URL processing.")
        processed_audio = download_audio(audio_url)
    elif audio_method == 2:
        # Existing MP3 file
        if not mp3_file:
            raise ValueError("An MP3 file path is required.")
        processed_audio = mp3_file
    elif audio_method == 3:
        # Subtitle file (SRT or VTT) for translation only.
        if not srt_file:
            raise ValueError("A subtitle file path is required.")
        process_subtitle(srt_file, translate_flag=1)
        return
    else:
        raise ValueError("Invalid audio_method value.")

    # Transcription step (if not skipped)
    segments = None
    detected_lang = None
    if transcribe_flag == 1:
        base_name = os.path.splitext(os.path.basename(processed_audio))[0]
        transcript_path = os.path.join("transcripts", f"original_{base_name}.vtt")
        if transcription_method == 1:
            segments, detected_lang = transcribe_audio(processed_audio, transcript_path)
        elif transcription_method == 2:
            # Use local_whisper from local_transcribe.py – assuming it has the same signature.
            try:
                from local_transcribe import local_whisper
            except ImportError:
                print("local_whisper function not found in local_transcribe.py")
                return
            segments, detected_lang = local_whisper(processed_audio, transcript_path)
        elif transcription_method == 3:
            if forced_lang is None:
                raise ValueError("Forced language code must be provided for transcription_method 3.")
            segments, detected_lang = transcribe_audio(processed_audio, transcript_path, language_code=forced_lang)
        else:
            raise ValueError("Invalid transcription_method.")
        if segments is None or detected_lang is None:
            print("Error: Transcription failed.")
            return
    elif transcribe_flag == 0:
        if audio_method != 3:
            raise ValueError("Transcription skipped but input is not a subtitle file.")
    else:
        raise ValueError("Invalid transcribe flag value.")

    # Translation step (if requested)
    if translate_flag and segments and detected_lang:
        translate_srt(segments, detected_lang, target_lang="en", audio_file=processed_audio)
    else:
        print("Skipping translation.")

# ---------------------
# COMMAND-LINE INTERFACE
# ---------------------
def main():
    parser = argparse.ArgumentParser(
        description="Command-line tool to process video, audio, or subtitle files for transcription and/or translation."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=str, help="Path to an input file (video, MP3, or VTT)")
    group.add_argument("--dir", type=str, help="Directory containing video files (MP4/MOV) to process")
    group.add_argument("--youtube", type=str, help="YouTube or audio URL to download and process")
    # Flags to specify type of input file
    parser.add_argument("--vtt", action="store_true", help="Input file is a VTT file (translation only; ignores local flag)")
    parser.add_argument("--mp3", action="store_true", help="Input file is an MP3 file")
    # Processing options
    parser.add_argument("--local", "-l", action="store_true", help="Run local Whisper transcription (ignored if --vtt is used)")
    parser.add_argument("--translate", "-t", action="store_true", help="Include translation API call and generate translated VTT")
    parser.add_argument("--lang", type=str, help="Forced language code (e.g., 'en', 'es') for transcription")
    args = parser.parse_args()

    # Determine the transcription method.
    # If forced language is provided, we use transcription_method 3.
    if args.lang:
        transcription_method = 3
        forced_lang = args.lang
    else:
        # Use local transcription if --local is provided; otherwise, default to API.
        transcription_method = 2 if args.local else 1
        forced_lang = None

    # Process based on the input source.
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
        # For subtitles, translation is implicit.
        process_audio(
            audio_method=3,
            srt_file=args.file,
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
        # Process all .mp4 and .mov files in the provided directory.
        directory = args.dir
        video_extensions = ("*.mp4", "*.mov")
        files = []
        for ext in video_extensions:
            files.extend(glob.glob(os.path.join(directory, ext)))
        if not files:
            print(f"No video files found in directory: {directory}")
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
        # Default: process a single file. Assume it's a video unless other flags are provided.
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
