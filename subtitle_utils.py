import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip
from pydub import AudioSegment
import speech_recognition as sr
from moviepy.config import change_settings
import requests
import time
import assemblyai as aai

change_settings({"IMAGEMAGICK_BINARY": "C:\Program Files (x86)\ImageMagick-7.1.1-Q16\magick.exe"})

# Function to extract audio from video
def extract_audio_from_video(input_video: str, output_audio: str):
    try:
        print(f"Extracting audio from video: {input_video} -> {output_audio}")
        video_clip = VideoFileClip(input_video)
        video_clip.audio.write_audiofile(output_audio, codec="libmp3lame")
        print("Audio extraction completed.")
    except Exception as e:
        print(f"Error during audio extraction: {e}")
        raise

# Function to convert audio to PCM WAV format
def convert_audio_to_wav(input_audio: str, output_audio: str):
    try:
        print(f"Converting audio to WAV: {input_audio} -> {output_audio}")
        audio = AudioSegment.from_file(input_audio)
        audio = audio.set_channels(1)  # Ensure mono audio
        audio = audio.set_frame_rate(16000)  # Standard sample rate for transcription
        audio.export(output_audio, format="wav")
        print("Audio conversion completed.")
    except Exception as e:
        print(f"Error during audio conversion: {e}")
        raise

# Function to transcribe audio using SpeechRecognition
def transcribe_audio_with_word_timestamps(audio_file: str):
    """
    Transcribe audio with word-level timestamps using AssemblyAI.
    Args:
        audio_file (str): Path to the local audio file or a publicly accessible URL.
    Returns:
        List[aai.Word]: List of word objects with timestamps from AssemblyAI.
    """
    try:
        # Set your AssemblyAI API key
        aai.settings.api_key = ""

        # Create a transcription configuration
        config = aai.TranscriptionConfig(
            punctuate=True,
            format_text=True
        )

        # Initialize the transcriber with the configuration
        transcriber = aai.Transcriber(config=config)

        # Start transcription
        print(f"Starting transcription for: {audio_file}")
        transcript = transcriber.transcribe(audio_file)

        # Check the status of the transcription
        if transcript.status == aai.TranscriptStatus.error:
            print(f"Transcription failed: {transcript.error}")
            raise Exception(f"Transcription error: {transcript.error}")

        print("Transcription completed.")
        return transcript.words  # Return the word objects with timestamps

    except Exception as e:
        print(f"Error during transcription: {e}")
        raise

# Function to generate quick captions
def generate_dynamic_captions_from_words(words, words_per_caption=3, gap_threshold=1.0, long_word_length=7):
    """
    Generate dynamic captions based on word-level timestamps, adjusting for pauses and long words.
    Args:
        words (List[aai.Word]): List of Word objects from AssemblyAI.
        words_per_caption (int): Maximum number of words per caption.
        gap_threshold (float): Time gap in seconds to consider a new caption.
        long_word_length (int): Minimum length of a word to consider it "long".
    Returns:
        List[Tuple[float, float, str]]: Captions as (start_time, end_time, text).
    """
    captions = []
    buffer = []
    start_time = None

    for i, word in enumerate(words):
        # Start timing for the first word in the buffer
        if not start_time:
            start_time = word.start / 1000.0  # Convert milliseconds to seconds

        buffer.append(word.text)

        # Identify if the word is long
        is_long_word = len(word.text) >= long_word_length

        # Check if the current word should end the caption
        is_last_word = (i == len(words) - 1)
        next_word_gap = (words[i + 1].start / 1000.0 - word.end / 1000.0) if not is_last_word else 0

        # Dynamic captioning conditions
        if (
            len(buffer) == words_per_caption or               # Standard condition: buffer full
            is_last_word or                                   # Last word in the sequence
            next_word_gap > gap_threshold or                 # Pause detected
            (is_long_word and len(buffer) >= 1)              # Special case: long word triggers a single-word caption
        ):
            # End caption here
            end_time = word.end / 1000.0  # Convert milliseconds to seconds
            caption_text = " ".join(buffer)
            captions.append((start_time, end_time, caption_text))
            buffer = []  # Reset buffer
            start_time = None  # Reset start time for the next caption

    print(f"Generated {len(captions)} captions.")
    return captions

# Function to overlay captions onto video
def add_quick_captions_to_video_with_music(video_path: str, captions, output_video_path: str, background_music_path: str, fade_duration=0.1):
    """
    Overlay captions onto the video and add looping background music.
    Args:
        video_path (str): Path to the input video.
        captions (list): List of (start_time, end_time, text) tuples.
        output_video_path (str): Path to save the output video.
        background_music_path (str): Path to the background music file (MP3).
        fade_duration (float): Duration of the fade effect in seconds.
    """
    try:
        print(f"Processing video: {video_path} with captions and music")
        video = VideoFileClip(video_path)
        subtitle_clips = []

        # Add captions to the video
        for start_time, end_time, text in captions:
            subtitle = (TextClip(text, fontsize=75,  # Font size in 'vmin' relative to video height
                                 color='#ffffff',  # Fill color
                                 font='./Montserrat-Bold.otf',  # Font family
                                 stroke_color='#000000',  # Stroke color
                                 stroke_width=3))  # Stroke width in 'vmin'

            # Position at the bottom with padding
            subtitle = (subtitle
                        .set_position(('center', video.size[1] - subtitle.size[1] - video.size[1] * 0.25))  # Bottom padding
                        .set_duration(end_time - start_time)
                        .set_start(start_time))
            subtitle = subtitle.crossfadein(fade_duration).crossfadeout(fade_duration)  # Add fade effect
            subtitle_clips.append(subtitle)

        # Combine the video and subtitle clips
        video_with_subtitles = CompositeVideoClip([video, *subtitle_clips])

        # Add background music
        print(f"Adding background music from: {background_music_path}")
        background_music = AudioFileClip(background_music_path)

        # Adjust the volume of the background music
        background_music = background_music.volumex(0.02)  # Set music volume

        # Handle music longer or shorter than video duration
        duration = video.duration
        if background_music.duration < duration:
            # Loop music to match video duration
            looped_music = background_music.fx(AudioFileClip.loop, duration=duration)
        else:
            # Trim music to match video duration
            looped_music = background_music.subclip(0, duration)

        # Combine the video's original audio with the background music
        final_audio = CompositeAudioClip([video_with_subtitles.audio, looped_music])
        video_with_subtitles = video_with_subtitles.set_audio(final_audio)

        # Export the final video
        video_with_subtitles.write_videofile(output_video_path, codec="libx264", audio_codec="aac")
        print(f"Video saved at: {output_video_path}")

    except Exception as e:
        print(f"Error processing video with captions and music: {e}")
        raise

# Main function to process video and add captions
def auto_caption(input_video: str):
    try:
        print(f"Processing video: {input_video}")
        video_name = os.path.splitext(os.path.basename(input_video))[0]
        audio_path = f"./output/audio/{video_name}.mp3"
        wav_path = f"./output/audio/{video_name}.wav"
        output_video_path = f"./output/{video_name}_captioned.mp4"

        # Ensure directories exist
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        os.makedirs(os.path.dirname(output_video_path), exist_ok=True)

        # Step 1: Extract audio from video
        extract_audio_from_video(input_video, audio_path)

        # Step 2: Convert MP3 to WAV
        convert_audio_to_wav(audio_path, wav_path)

        # Step 3: Transcribe audio to get word-level timestamps
        words = transcribe_audio_with_word_timestamps(wav_path)

        # Step 4: Generate captions from word timestamps
        captions = generate_dynamic_captions_from_words(words)
        print(f"First few captions: {captions[:5]}")  # Debugging output

        # Step 5: Add captions to video
        add_quick_captions_to_video_with_music(input_video, captions, output_video_path,  background_music_path="./background.mp3",)

        print(f"Captioned video saved at: {output_video_path}")
        return output_video_path
    except Exception as e:
        print(f"Error during auto-captioning: {e}")
        raise
