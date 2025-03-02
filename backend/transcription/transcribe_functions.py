import os
import requests
import subprocess
from google.cloud import translate_v2 as translate
from datetime import datetime
import yt_dlp as youtube_dl

# Set up Google Translate credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.expanduser("")
google_client = translate.Client()

# Your OpenAI API key
OPENAI_API_KEY = ""

# Generate unique timestamp
def get_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# Convert seconds to SRT timestamp format
def format_srt_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millisecs:03}"

# Function to extract audio from .MOV to .MP3
def extract_audio_from_video(input_path):
    output_audio_path = os.path.splitext(input_path)[0] + ".mp3"
    command = [
        "ffmpeg",
        "-i", input_path,  # Input video file
        "-vn",  # Disable video recording (only extract audio)
        "-acodec", "mp3",  # Specify the audio codec (MP3)
        "-ar", "44100",  # Audio sample rate (adjust if needed)
        "-ac", "2",  # Number of audio channels (stereo)
        output_audio_path  # Output path for the audio file
    ]
    subprocess.run(command)
    return output_audio_path

# Transcribe audio using OpenAI Whisper API
def transcribe_audio(audio_path, transcript_path, language_code=None):
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    # Parameters (non-file) go in the data dictionary.
    data = {
        "model": "whisper-1",
        "response_format": "verbose_json",
        "timestamp_granularities": "segment"
    }
    if language_code:
        data["language"] = language_code  # Force Whisper to use this language code
    
    files = {
        "file": open(audio_path, "rb")
    }
    
    try:
        response = requests.post(url, headers=headers, data=data, files=files)
        files["file"].close()
        if response.status_code == 200:
            result = response.json()
            detected_language = result.get("language", "unknown")
            if "segments" not in result:
                return None, None

            segments = result["segments"]
            srt_segments = []
            segment_number = 1
            for segment in segments:
                start_time = format_srt_timestamp(segment["start"])
                end_time = format_srt_timestamp(segment["end"])
                text = segment["text"]
                srt_segments.append((segment_number, start_time, end_time, text))
                segment_number += 1

            with open(transcript_path, "w", encoding="utf-8") as file:
                for idx, start_time, end_time, text in srt_segments:
                    file.write(f"{idx}\n{start_time} --> {end_time}\n{text}\n\n")
            return srt_segments, detected_language
        else:
            print(f"Error: {response.status_code} response: {response.text}")
            return None, None
    except Exception as e:
        print(f"Exception during transcription: {e}")
        return None, None

# Google Translate API call
def translate_text_google(text_list, target_language="en"):
    if isinstance(text_list, list):
        result = google_client.translate(text_list, target_language=target_language)
        return [res['translatedText'] for res in result]
    result = google_client.translate(text_list, target_language=target_language)
    return result['translatedText']

# Translate and save SRT
def translate_srt(segments, source_lang, target_lang="en", audio_file=None):
    texts = [segment[3] for segment in segments]
    translated_texts = translate_text_google(texts, target_lang)

    translated_srt_path = f"transcripts/{os.path.splitext(os.path.basename(audio_file))[0]}_{get_timestamp()}_en.srt"
    with open(translated_srt_path, "w", encoding="utf-8") as file:
        for idx, (index, start_time, end_time, _) in enumerate(segments):
            file.write(f"{index}\n{start_time} --> {end_time}\n{translated_texts[idx]}\n\n")

# Convert youtube url to mp3
def download_audio(youtube_url):
    """Downloads audio from a YouTube video and converts it to MP3 format."""
    output_path = "audio_files/audio.mp3"  # Ensure MP3 format

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': "audio_files/audio",  # Temp file before conversion
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',  # Force MP3 format
            'preferredquality': '192',
        }],
    }

    print("Downloading YouTube audio as MP3...")
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])

    print(f"Audio saved as: {output_path}")

    return output_path  # Return the MP3 file path

# given an srt, parse into segments
def parse_srt(srt_file_path):
    """Parse an SRT file and return a list of segments."""
    segments = []

    try:
        with open(srt_file_path, "r", encoding="utf-8") as file:
            content = file.read().strip()

        # Split the content by blank lines to separate each subtitle block
        subtitle_blocks = content.split('\n\n')

        for block in subtitle_blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                index = int(lines[0].strip())  # Subtitle index
                times = lines[1].strip()  # Time range, format: start --> end
                start_time, end_time = times.split(' --> ')
                text = ' '.join(lines[2:]).strip()  # Combine any multiline text
                segments.append((index, start_time, end_time, text))

    except Exception as e:
        print(f"Error parsing SRT file: {e}")
        return None

    return segments

