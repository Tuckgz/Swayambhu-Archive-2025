import os
import requests
from datetime import datetime
from google.cloud import translate_v2 as translate
import subprocess

# Set the working directory to 'backend' (relative path)
os.chdir(os.path.join(os.getcwd(), "backend"))

# Ensure required directories exist
os.makedirs("audio_files", exist_ok=True)
os.makedirs("transcripts", exist_ok=True)

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
def transcribe_audio(audio_path, transcript_path):
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    files = {
        "file": open(audio_path, "rb"),
        "model": (None, "whisper-1"),
        "response_format": (None, "verbose_json"),
        "timestamp_granularities": (None, "segment")  # Set granularity to "segment"
    }

    try:
        response = requests.post(url, headers=headers, files=files)
        files["file"].close()

        if response.status_code == 200:
            result = response.json()
            print("API Response: ", result)  # Log the entire response to inspect it
            detected_language = result.get("language", "unknown")
            print(f"Detected language: {detected_language}")

            # Check if 'segments' exists in the response
            if "segments" not in result:
                print("Error: No 'segments' found in API response.")
                return None, None

            segments = result["segments"]
            srt_segments = []

            # Build SRT file segments
            segment_number = 1
            for segment in segments:
                start_time = format_srt_timestamp(segment["start"])
                end_time = format_srt_timestamp(segment["end"])
                text = segment["text"]
                srt_segments.append((segment_number, start_time, end_time, text))
                segment_number += 1

            # Write to SRT file
            with open(transcript_path, "w", encoding="utf-8") as file:
                for idx, start_time, end_time, text in srt_segments:
                    file.write(f"{idx}\n{start_time} --> {end_time}\n{text}\n\n")

            print(f"Saved transcription to {transcript_path}")
            return srt_segments, detected_language
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None, None

    except Exception as e:
        print(f"Error during transcription: {e}")
        return None, None

# Google Translate API call
def translate_text_google(text_list, target_language="en"):
    if isinstance(text_list, list):
        result = google_client.translate(text_list, target_language=target_language)
        return [res['translatedText'] for res in result]
    result = google_client.translate(text_list, target_language=target_language)
    return result['translatedText']

# Translate and save SRT
def translate_srt(segments, source_lang, target_lang="en"):
    texts = [segment[3] for segment in segments]
    translated_texts = translate_text_google(texts, target_lang)

    translated_srt_path = f"transcripts/{os.path.splitext(os.path.basename(audio_file))[0]}_{get_timestamp()}_en.srt"
    with open(translated_srt_path, "w", encoding="utf-8") as file:
        for idx, (index, start_time, end_time, _) in enumerate(segments):
            file.write(f"{index}\n{start_time} --> {end_time}\n{translated_texts[idx]}\n\n")

    print(f"Saved translated SRT to {translated_srt_path}")

# Example usage
audio_file = "audio_files/IMG_8406.mov"  # Change this to the actual MOV file path

# Extract audio from the MOV file
audio_mp3 = extract_audio_from_video(audio_file)

# Generate SRT file path
srt_file = f"transcripts/original_{os.path.splitext(os.path.basename(audio_file))[0]}.srt"

# Transcribe audio
segments, detected_lang = transcribe_audio(audio_mp3, srt_file)

if segments and detected_lang:
    srt_file = f"transcripts/original_{os.path.splitext(os.path.basename(audio_file))[0]}_{detected_lang}.srt"
    print(f"Transcription for {audio_file} complete.")
    translate_srt(segments, detected_lang, "en")  # Translate to English
