# constants.py

import os

# Get the directory where this script (constants.py) is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Get the parent directory (reddit-parser/)
BASE_DIR = os.path.dirname(SCRIPT_DIR)

# Define paths relative to BASE_DIR to ensure all resources are siblings
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio")
INPUT_VIDEO = os.path.join(BASE_DIR, "videoplayback.mp4")
STORIES_FILE = os.path.join(BASE_DIR, "stories.txt")

# Path to FFmpeg executable
FFMPEG_PATH = "C:/ffmpeg/bin/ffmpeg.exe"  # Ensure this path is correct
