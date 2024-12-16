# main.py

import os
import logging
import subprocess

from tts_utils import synthesize_speech
from ffmpeg_utils import create_video, combine_audio_video
from story_parser import read_stories

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("processing.log"),
            logging.StreamHandler()
        ]
    )

    # Define file paths
    STORIES_FILE = "C:\\Users\\lisof\\Desktop\\reddit-parser\\stories.txt"  # Update this path accordingly
    OUTPUT_DIR = "C:\\Users\\lisof\\Desktop\\reddit-parser\\output"        # Update this path accordingly
    AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio")
    INPUT_VIDEO = "C:\\Users\\lisof\\Desktop\\reddit-parser\\videoplayback.webm"  # Update as needed

    # Ensure output directories exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)

    # Read stories from file
    stories = read_stories(STORIES_FILE)
    if not stories:
        logging.error("No stories found in the STORIES_FILE.")
        return

    # Generate videos for each story
    for i, story in enumerate(stories, start=1):
        audio_file = os.path.join(AUDIO_DIR, f"story_{i}.mp3")
        temp_video = os.path.join(OUTPUT_DIR, f"temp_story_{i}.mp4")
        output_video = os.path.join(OUTPUT_DIR, f"story_{i}.mp4")

        # Synthesize speech and get its duration
        logging.info("Synthesizing speech for story %d...", i)
        try:
            speech_duration = synthesize_speech(story, audio_file, 'en-US-ChristopherNeural')
            logging.info("Speech duration for story %d: %.2f seconds", i, speech_duration)
        except Exception as e:
            logging.error("Failed to synthesize speech for story %d: %s", i, e)
            continue  # Skip to the next story

        # Create a video that matches the duration of the speech
        logging.info("Generating base video for story %d...", i)
        try:
            create_video(
                input_video=INPUT_VIDEO,
                output_video=temp_video,
                desired_duration=speech_duration,
                fps=30,               # Set desired fps
                target_width=1080,    # 9:16 width
                target_height=1920,   # 9:16 height
                crf=25,               # Quality setting
                preset="slow"         # Encoding preset
            )
            logging.info("Base video created at: %s", temp_video)
        except subprocess.CalledProcessError as e:
            logging.error("FFmpeg failed to create video for story %d: %s", i, e)
            continue  # Skip to the next story
        except Exception as e:
            logging.error("Failed to create video for story %d: %s", i, e)
            continue  # Skip to the next story

        # Combine the synthesized speech with the generated video
        logging.info("Combining audio and video for story %d...", i)
        try:
            combine_audio_video(audio_file, temp_video, output_video)
            logging.info("Combined video saved at: %s", output_video)
        except subprocess.CalledProcessError as e:
            logging.error("FFmpeg failed to combine audio and video for story %d: %s", i, e)
            continue  # Skip to the next story
        except Exception as e:
            logging.error("Failed to combine audio and video for story %d: %s", i, e)
            continue  # Skip to the next story

        # Remove the temporary video file
        try:
            os.remove(temp_video)
            logging.info("Removed temporary video file for story %d.", i)
        except Exception as e:
            logging.warning("Failed to remove temporary video file for story %d: %s", i, e)

    logging.info("All stories have been processed successfully.")


if __name__ == "__main__":
    main()