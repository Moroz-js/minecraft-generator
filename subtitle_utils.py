# subtitle_utils.py

from moviepy.editor import ( # type: ignore
    VideoFileClip,
    TextClip,
    CompositeVideoClip,
    ColorClip,
    ImageClip,
    concatenate_videoclips
)
from moviepy.config import change_settings
from moviepy.video.fx import fadein, fadeout
from PIL import Image, ImageDraw, ImageFont
import os
import math
import numpy as np  # Added import for NumPy


# Ensure ImageMagick is correctly set up
change_settings({"IMAGEMAGICK_BINARY": r"C:\\Program Files (x86)\\ImageMagick-7.1.1-Q16\\magick.exe"})


def auto_caption(
    input_video: str
):
    return input_video


