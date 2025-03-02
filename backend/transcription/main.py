import os
from transcribe_functions import (
    extract_audio_from_video,
    transcribe_audio,
    translate_srt,
    get_timestamp,
    download_audio,
    parse_srt
)
from local_transcribe import local_whisper  # Skeleton function in local_transcribe.py

# Set the working directory to 'backend' (relative path)
os.chdir(os.path.join(os.getcwd(), "backend"))

# Ensure required directories exist
os.makedirs("audio_files", exist_ok=True)
os.makedirs("transcripts", exist_ok=True)

def adjust_filepath(filepath):
    """
    Adjust the provided file path to remove the 'backend/' part if it starts with it.
    """
    if filepath.startswith("backend/"):
        return filepath[len("backend/"):]
    return filepath

def process_audio(
    audio_method,          # 0 = MOV/MP4 (video file), 1 = Audio URL, 2 = MP3 file, 3 = SRT file
    audio_url=None,        # Used if audio_method is 1
    audio_file=None,       # Used if audio_method is 0 (video file)
    mp3_file=None,         # Used if audio_method is 2 (existing MP3 file)
    srt_file=None,         # Used if audio_method is 3 (existing SRT file)
    transcribe=1,          # 1 to run transcription, 0 to skip transcription
    transcription_method=1,# 1 = Whisper API, 2 = Local Whisper, 3 = Whisper API (Forced Language); 0 = skip (only valid with audio_method 3)
    translate=1,           # 1 to translate, 0 to skip translation
    forced_lang=None       # Forced language code (used if transcription_method==3)
):
    """
    Handles the entire process based on the selected method and options.
    """
    # Adjust file paths if necessary
    if audio_file:
        audio_file = adjust_filepath(audio_file)
    if mp3_file:
        mp3_file = adjust_filepath(mp3_file)
    if srt_file:
        srt_file = adjust_filepath(srt_file)

    # Step 1: Determine audio source
    if audio_method == 0:
        # Process MOV/MP4 video file (audio_file must be provided)
        if not audio_file:
            raise ValueError("A video file path must be provided for audio_method 0.")
        processed_audio = extract_audio_from_video(audio_file)
    elif audio_method == 1:
        # Process audio from an URL (e.g., YouTube)
        if not audio_url:
            raise ValueError("audio_url must be provided for audio_method 1.")
        processed_audio = download_audio(audio_url)
    elif audio_method == 2:
        # Use existing MP3 file
        if not mp3_file:
            raise ValueError("An MP3 file path must be provided for audio_method 2.")
        processed_audio = mp3_file
    elif audio_method == 3:
        # Use existing SRT file directly
        if not srt_file:
            raise ValueError("An SRT file path must be provided for audio_method 3.")
        segments = parse_srt(srt_file)
        if translate == 1 and segments:
            translate_srt(segments, source_lang="unknown", target_lang="en", audio_file=srt_file)
        else:
            print("Skipping translation.")
        return
    else:
        raise ValueError("Invalid audio_method. Must be 0, 1, 2, or 3.")

    # Step 2: Handle transcription if enabled
    segments = None
    detected_lang = None
    if transcribe == 1:
        base_name = os.path.splitext(os.path.basename(processed_audio))[0]
        srt_path = f"transcripts/original_{base_name}.srt"
        if transcription_method == 1:
            segments, detected_lang = transcribe_audio(processed_audio, srt_path)
            new_srt_path = f"transcripts/original_{base_name}_{get_timestamp()}_{detected_lang}.srt"
            os.rename(srt_path, new_srt_path)  # Rename the file on disk
            srt_path = new_srt_path
        elif transcription_method == 2:
            segments, detected_lang = local_whisper(processed_audio, srt_path)
        elif transcription_method == 3:
            if forced_lang is None:
                raise ValueError("For transcription_method 3 (Forced Language), a language code must be provided.")
            segments, detected_lang = transcribe_audio(processed_audio, srt_path, language_code=forced_lang)
            new_srt_path = f"transcripts/original_{base_name}_{get_timestamp()}_{forced_lang}.srt"
            os.rename(srt_path, new_srt_path)
            srt_path = new_srt_path
        else:
            raise ValueError("Invalid transcription_method. Must be 1, 2, or 3 when transcribe==1.")
        
        if segments is None or detected_lang is None:
            print("Error: Transcription failed. No segments were returned.")
            return
    elif transcribe == 0:
        if audio_method != 3:
            raise ValueError("Transcription is skipped, but audio_method is not 3. Please provide an SRT file.")
    else:
        raise ValueError("Invalid value for transcribe parameter.")

    # Step 3: Handle translation if enabled
    if translate == 1 and segments and detected_lang:
        translate_srt(segments, detected_lang, target_lang="en", audio_file=processed_audio)
    else:
        print("Skipping translation.")

def process_srt(srt_file, translate):
    with open(srt_file, "r", encoding="utf-8") as file:
        segments = parse_srt(file)
    if translate == 1 and segments:
        translate_srt(segments, source_lang="unknown", target_lang="en", audio_file=srt_file)
    else:
        print("Skipping translation.")

if __name__ == "__main__":
    # Prompt for audio method
    audio_method = int(input("Enter audio method (0 = MOV/MP4, 1 = Audio URL, 2 = MP3, 3 = SRT): "))
    
    # Initialize variables for each method
    audio_url = None
    video_file = None
    mp3_file = None
    srt_file = None

    if audio_method == 0:
        video_file = input("Enter video file path (MOV/MP4): ").strip() or None
    elif audio_method == 1:
        audio_url = input("Enter YouTube or other audio URL: ").strip() or None
    elif audio_method == 2:
        mp3_file = input("Enter MP3 file path: ").strip() or None
    elif audio_method == 3:
        srt_file = input("Enter SRT file path: ").strip() or None
    else:
        raise ValueError("Invalid audio method selected.")

    # Prompt for transcription method only if it's not an SRT file (audio_method != 3)
    transcription_method = 0
    transcribe_flag = 0
    forced_lang = None
    if audio_method != 3:
        transcription_method = int(input("Enter transcription method (0 = None, 1 = Whisper API, 2 = Local Whisper, 3 = Whisper API - Forced Language): "))
        transcribe_flag = 0 if transcription_method == 0 else 1
        if transcription_method == 3:
            forced_lang = input("Enter the language code for forced transcription (e.g., 'en', 'es'): ").strip()
    else:
        transcription_method = 0
        transcribe_flag = 0

    translate_option = int(input("Enter translation option (1 = Translate, 0 = Skip translation): "))
    
    process_audio(
        audio_method=audio_method,
        audio_url=audio_url,
        audio_file=video_file,
        mp3_file=mp3_file,
        srt_file=srt_file,
        transcribe=transcribe_flag,
        transcription_method=transcription_method,
        translate=translate_option,
        forced_lang=forced_lang
    )
