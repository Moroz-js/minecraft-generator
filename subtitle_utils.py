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


def create_highlighted_text_image(
    line: str,
    highlight_word_index: int,
    font_path: str,
    font_size: int,
    text_color: str,
    highlight_color: str,
    background_color: tuple,
    image_size: tuple,
):
    """
    Create an image of the text line with the word at highlight_word_index highlighted.

    Args:
        line (str): The full line of text.
        highlight_word_index (int): The index of the word to highlight.
        font_path (str): Path to the font file.
        font_size (int): Font size.
        text_color (str): Color of regular text.
        highlight_color (str): Color of highlighted text.
        background_color (tuple): Background color as (R, G, B).
        image_size (tuple): Size of the image as (width, height).

    Returns:
        PIL.Image: Image with highlighted word.
    """
    img = Image.new("RGB", image_size, color=background_color)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        # Fallback to a default PIL font if the specified font is not found
        font = ImageFont.load_default()

    words = line.split()
    x_offset = 0
    y_offset = (image_size[1] - font_size) // 2  # Center vertically

    for i, word in enumerate(words):
        if i == highlight_word_index:
            color = highlight_color
        else:
            color = text_color
        # Measure the size of the word
        word_size = draw.textsize(word + " ", font=font)
        # Draw the word
        draw.text((x_offset, y_offset), word + " ", font=font, fill=color)
        x_offset += word_size[0]

    return img


def split_text_into_lines(story_text: str, max_words_per_line: int = 5):
    """
    Split the story_text into lines with a maximum number of words per line.

    Args:
        story_text (str): The full story text.
        max_words_per_line (int): Maximum number of words per line.

    Returns:
        List[str]: List of subtitle lines.
    """
    words = story_text.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        if len(current_line) >= max_words_per_line:
            lines.append(" ".join(current_line))
            current_line = []
    if current_line:
        lines.append(" ".join(current_line))
    return lines


def extend_video_duration(clip: VideoFileClip, target_duration: float) -> VideoFileClip:
    """
    Extend the video duration to match the target duration by looping the video.

    Args:
        clip (VideoFileClip): The original video clip.
        target_duration (float): The desired duration in seconds.

    Returns:
        VideoFileClip: The extended video clip.
    """
    if clip.duration >= target_duration:
        return clip.subclip(0, target_duration)
    else:
        # Loop the video as many times as needed
        n_loops = math.ceil(target_duration / clip.duration)
        extended_clips = [clip] * n_loops
        extended_clip = concatenate_videoclips(extended_clips).subclip(0, target_duration)
        return extended_clip


def create_dynamic_subtitles(input_video: str, story_text: str, audio_duration: float, output_video: str):
    """
    Create dynamic subtitles for a video, splitting text into short lines and highlighting words.

    Args:
        input_video (str): Path to the input video file.
        story_text (str): The full story text for subtitles.
        audio_duration (float): Duration of the audio in seconds.
        output_video (str): Path to save the output video with subtitles.
    """
    # Desired final resolution for 9:16
    target_width = 1080
    target_height = 1920  # 9:16 ratio

    # Load the input video
    clip = VideoFileClip(input_video)
    input_duration = clip.duration  # Get the actual duration of the input video

    # Adjust video duration to match audio duration
    clip_extended = extend_video_duration(clip, audio_duration)

    # Calculate target aspect ratio
    target_ratio = target_width / target_height

    # Crop the video to 9:16 without adding borders
    original_width, original_height = clip_extended.size
    original_ratio = original_width / original_height

    if original_ratio > target_ratio:
        # Video is wider than target ratio; fit height and crop width
        new_height = target_height
        new_width = int(new_height * original_ratio)
    else:
        # Video is taller than target ratio; fit width and crop height
        new_width = target_width
        new_height = int(new_width / original_ratio)

    # Resize the clip to ensure the target dimension is covered
    clip_resized = clip_extended.resize(height=new_height) if original_ratio > target_ratio else clip_extended.resize(width=new_width)

    # Calculate the cropping coordinates to center the video
    crop_x1 = (clip_resized.w - target_width) // 2
    crop_y1 = (clip_resized.h - target_height) // 2

    # Crop the video to 1080x1920
    clip_cropped = clip_resized.crop(x1=crop_x1, y1=crop_y1, width=target_width, height=target_height).set_duration(audio_duration)

    # Split story text into lines of 1-5 words
    lines = split_text_into_lines(story_text, max_words_per_line=5)
    if not lines:
        # If there's no text, write the cropped video directly
        clip_cropped.write_videofile(output_video, codec="libx264", audio_codec="aac")
        clip_cropped.close()
        clip_resized.close()
        clip_extended.close()
        clip.close()
        return

    # Calculate total number of words
    total_words = sum(len(line.split()) for line in lines)

    # Define per-word duration based on audio duration
    per_word_duration = audio_duration / total_words

    # Clamp per_word_duration between min and max for readability
    min_word_duration = 1.0  # seconds
    max_word_duration = 2.5  # seconds
    per_word_duration = max(min_word_duration, min(per_word_duration, max_word_duration))

    # Recalculate total subtitle duration
    total_subtitle_duration = total_words * per_word_duration

    # Adjust per_word_duration if necessary to fit the audio duration
    if total_subtitle_duration < audio_duration:
        per_word_duration = audio_duration / total_words
    elif total_subtitle_duration > audio_duration:
        per_word_duration = audio_duration / total_words  # Ensures total duration matches

    # Font settings
    # Ensure the font file exists; adjust the path if necessary
    # Common font paths:
    # Windows: "C:\\Windows\\Fonts\\arialbd.ttf"
    # macOS: "/Library/Fonts/Arial Bold.ttf"
    # Linux: "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_path = "C:\\Windows\\Fonts\\arialbd.ttf"  # Update this path if necessary
    font_size = 70
    text_color = "white"
    highlight_color = "yellow"
    background_color = (0, 0, 0)  # Black background for text image
    image_width = target_width - 100
    image_height = 200  # Adjust as needed
    image_size = (image_width, image_height)

    # Position settings
    text_position = ("center", target_height - image_height - 50)  # Adjust vertical position as needed

    text_clips = []
    current_time = 0.0

    for line in lines:
        words = line.split()
        for idx, word in enumerate(words):
            # Create image with the current word highlighted
            img = create_highlighted_text_image(
                line=line,
                highlight_word_index=idx,
                font_path=font_path,
                font_size=font_size,
                text_color=text_color,
                highlight_color=highlight_color,
                background_color=background_color,
                image_size=image_size,
            )

            # Convert PIL image to numpy array
            img_np = np.array(img)

            # Create an ImageClip from the numpy array
            txt_clip = (
                ImageClip(img_np)
                .set_duration(per_word_duration)
                .set_start(current_time)
                .set_position(text_position)
                .crossfadein(0.1)
                .crossfadeout(0.1)
            )
            text_clips.append(txt_clip)

            current_time += per_word_duration

    # Composite all clips
    final_composite = CompositeVideoClip([clip_cropped, *text_clips]).set_duration(audio_duration)

    # Write the final video
    final_composite.write_videofile(output_video, codec="libx264", audio_codec="aac")

    # Cleanup
    final_composite.close()
    clip_cropped.close()
    clip_resized.close()
    clip_extended.close()
    clip.close()