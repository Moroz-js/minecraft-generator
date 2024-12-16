import os
import logging
import subprocess

from tts_utils import synthesize_speech
from ffmpeg_utils import create_video, combine_audio_video
from story_parser import read_stories
from subtitle_utils import auto_caption

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("processing.log"),
            logging.StreamHandler()
        ]
    )

    STORIES_FILE = "C:\\Users\\lisof\\Desktop\\reddit-parser\\stories.txt"
    OUTPUT_DIR = "C:\\Users\\lisof\\Desktop\\reddit-parser\\output"
    AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio")
    INPUT_VIDEO = "C:\\Users\\lisof\\Desktop\\reddit-parser\\videoplayback.webm"

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)

    stories = read_stories(STORIES_FILE)
    if not stories:
        logging.error("No stories found in the STORIES_FILE.")
        return

    for story_index, story in enumerate(stories, start=1):
        try:
            # Generate audio file paths
            audio_file = os.path.join(AUDIO_DIR, f"story_{story_index}.mp3")
            temp_video = os.path.join(OUTPUT_DIR, f"temp_story_{story_index}.mp4")
            output_video = os.path.join(OUTPUT_DIR, f"story_{story_index}.mp4")

            # Speech Synthesis
            logging.info(f"Synthesizing speech for story {story_index}...")
            speech_duration = synthesize_speech(story, audio_file, 'en-US-ChristopherNeural')
            logging.info(f"Speech duration for story {story_index}: {speech_duration:.2f} seconds")

            # Video Creation
            logging.info(f"Generating base video for story {story_index}...")
            create_video(
                input_video=INPUT_VIDEO,
                output_video=temp_video,
                desired_duration=speech_duration,
                fps=60,
                target_width=1080,
                target_height=1920,
                crf=25,
                preset="slow"
            )
            logging.info(f"Base video created at: {temp_video}")

            # Combine Audio and Video
            logging.info(f"Combining audio and video for story {story_index}...")
            combine_audio_video(audio_file, temp_video, output_video)
            logging.info(f"Combined video saved at: {output_video}")
        
            # Add Captions
            auto_caption(output_video)
            logging.info(f"Video with caption saved: {output_video}")

            # Remove Temporary Video
            try:
                os.remove(temp_video)
                logging.info(f"Removed temporary video file for story {story_index}.")
            except Exception as e:
                logging.warning(f"Failed to remove temporary video file for story {story_index}: {e}")

        except Exception as e:
            logging.error(f"Failed to process story {story_index}: {e}")
            continue

    logging.info("All stories have been processed successfully.")

if __name__ == "__main__":
    main()