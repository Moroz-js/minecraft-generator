# ffmpeg_utils.py

import os
import random
import logging
import subprocess
from constants import FFMPEG_PATH, OUTPUT_DIR

# ffmpeg_utils.py

import os
import random
import subprocess
from constants import FFMPEG_PATH, OUTPUT_DIR

def time_to_seconds(timestr: str) -> int:
    """
    Convert a time string (HH:MM:SS or MM:SS or SS) to total seconds.
    """
    parts = timestr.split(':')
    parts = [int(p) for p in parts]
    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        minutes, seconds = parts
        return minutes * 60 + seconds
    elif len(parts) == 3:
        hours, minutes, seconds = parts
        return hours * 3600 + minutes * 60 + seconds
    else:
        raise ValueError(f"Invalid time format: {timestr}")

def seconds_to_time(seconds: int) -> str:
    """
    Convert total seconds into a time string (HH:MM:SS).
    """
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def get_video_duration(input_video: str) -> float:
    """
    Retrieve the total duration of the input video in seconds using ffprobe.
    
    Args:
        input_video (str): Path to the input video file.
        
    Returns:
        float: Duration of the video in seconds.
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        input_video
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        duration = float(result.stdout.strip())
        print(f"[DEBUG] Total video duration: {duration} seconds")
        return duration
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to get video duration: {e.stderr}")
        raise

def create_video(input_video: str, output_video: str, desired_duration: float, fps: int = 24, target_width: int = 1080, target_height: int = 1920, crf: int = 20, preset: str = "slow", timeout: int = 600):
    """
    Generate a video clip with the specified duration and 9:16 aspect ratio, ensuring no borders.
    Re-encodes the video to embed fps metadata and apply scaling and cropping.

    Args:
        input_video (str): Path to the input video file.
        output_video (str): Path to save the generated video.
        desired_duration (float): Desired duration of the output video in seconds.
        fps (int, optional): Frames per second for the output video. Defaults to 24.
        target_width (int, optional): Width of the output video (default 1080 for 9:16). Defaults to 1080.
        target_height (int, optional): Height of the output video (default 1920 for 9:16). Defaults to 1920.
        crf (int, optional): Constant Rate Factor for quality (lower is better). Defaults to 20.
        preset (str, optional): Encoding preset for compression efficiency. Defaults to "slow".
        timeout (int, optional): Timeout for the FFmpeg command in seconds. Defaults to 300 (5 minutes).
    """
    # Verify input video exists
    if not os.path.exists(input_video):
        logging.error(f"Input video does not exist: {input_video}")
        raise FileNotFoundError(f"Input video not found: {input_video}")

    # Get total duration of the input video
    try:
        total_duration = get_video_duration(input_video)
    except Exception as e:
        logging.error(f"Error retrieving video duration: {e}")
        raise e

    if desired_duration > total_duration:
        error_msg = f"Desired duration ({desired_duration}s) exceeds total video duration ({total_duration}s)."
        logging.error(error_msg)
        raise ValueError(error_msg)

    # Choose a random start time
    max_start = total_duration - desired_duration
    start_sec = 1
    end_sec = start_sec + desired_duration

    logging.info(f"Selected random start time: {start_sec:.2f}s (End: {end_sec:.2f}s)")

    # Define scaling and cropping filter for 9:16 aspect ratio
    vf_filter = f"scale='if(gt(a,{target_width}/{target_height}),ceil({target_height}*a),{target_width})':'if(gt(a,{target_width}/{target_height}),{target_height},ceil({target_width}/a))', crop={target_width}:{target_height}"

    # Re-encode the video with specified fps, scaling, and cropping
    cut_cmd = [
        'ffmpeg', "-y",
        "-i", input_video,
        "-ss", f"{start_sec:.2f}",
        "-t", f"{desired_duration:.2f}",
        "-vf", vf_filter,            # Apply scaling and cropping
        "-c:v", "libx264",           # Re-encode video using H.264 codec
        "-preset", preset,           # Set encoding preset
        "-crf", str(crf),            # Set CRF for quality
        "-r", str(fps),              # Set frame rate
        "-pix_fmt", "yuv420p",       # Set pixel format
        "-profile:v", "high",        # Set H.264 profile
        "-an",                        # Disable audio stream
        output_video
    ]
    logging.info(f"Running FFmpeg command: {' '.join(cut_cmd)}")

    try:
        # Run the FFmpeg command with a timeout
        process = subprocess.run(cut_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
        
        logging.info(f"FFmpeg output: {process.stdout}")
        if process.stderr:
            logging.warning(f"FFmpeg warnings: {process.stderr}")
    except subprocess.TimeoutExpired:
        logging.error(f"FFmpeg command timed out after {timeout} seconds.")
        raise TimeoutError(f"FFmpeg command exceeded timeout of {timeout} seconds.")
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg failed to create video: {e.stderr}")
        raise e

# ======================= Old Function (Preserved as Comment) =======================

# def create_video(input_video: str, output_video: str, desired_duration: float, fps: int = 24, target_width: int = 1080, target_height: int = 1920, crf: int = 20, preset: str = "slow"):
#     """
#     Generate a video clip with the specified duration and 9:16 aspect ratio, ensuring no borders.
#     Re-encodes the video to embed fps metadata and apply scaling and cropping.
    
#     Args:
#         input_video (str): Path to the input video file.
#         output_video (str): Path to save the generated video.
#         desired_duration (float): Desired duration of the output video in seconds.
#         fps (int): Frames per second for the output video.
#         target_width (int): Width of the output video (default 1080 for 9:16).
#         target_height (int): Height of the output video (default 1920 for 9:16).
#         crf (int): Constant Rate Factor for quality (lower is better).
#         preset (str): Encoding preset for compression efficiency.
#     """
#     intervals = [
#         ("00:00", "1:05"),
#         ("1:05",  "2:10"),
#         ("2:10",  "4:37"),
#         ("4:37",  "8:24"),
#         # ("8:24",  "9:35"),
#     ]

#     chosen_interval = random.choice(intervals)
#     start_sec = time_to_seconds(chosen_interval[0])
#     end_sec = time_to_seconds(chosen_interval[1])
#     interval_length = end_sec - start_sec

#     print(f"[DEBUG] Chosen interval: {chosen_interval} (Start: {start_sec}s, End: {end_sec}s)")

#     # Define scaling and cropping filter for 9:16 aspect ratio
#     vf_filter = f"scale='if(gt(a,{target_width}/{target_height}),ceil({target_height}*a),{target_width})':'if(gt(a,{target_width}/{target_height}),{target_height},ceil({target_width}/a))', crop={target_width}:{target_height}"

#     if desired_duration <= interval_length:
#         # Re-encode the video with specified fps, scaling, and cropping
#         cut_cmd = [
#             FFMPEG_PATH, "-y",
#             "-i", input_video,
#             "-ss", seconds_to_time(start_sec),
#             "-t", str(desired_duration),
#             "-vf", vf_filter,            # Apply scaling and cropping
#             "-c:v", "libx264",           # Re-encode video using H.264 codec
#             "-preset", preset,           # Set encoding preset
#             "-crf", str(crf),            # Set CRF for quality
#             "-r", str(fps),              # Set frame rate
#             "-pix_fmt", "yuv420p",       # Set pixel format
#             "-profile:v", "high",        # Set H.264 profile
#             "-an",                        # Disable audio stream
#             output_video
#         ]
#         print(f"[DEBUG] Running FFmpeg command: {' '.join(cut_cmd)}")
#         subprocess.run(cut_cmd, check=True)
#         return

#     # If desired_duration > interval_length, loop the interval
#     repeat_count = int(desired_duration // interval_length) + 1
#     segment_file = os.path.join(OUTPUT_DIR, "temp_segment.mp4")
#     extract_cmd = [
#         FFMPEG_PATH, "-y",
#         "-i", input_video,
#         "-ss", seconds_to_time(start_sec),
#         "-t", str(interval_length),
#         "-vf", vf_filter,            # Apply scaling and cropping
#         "-c:v", "libx264",           # Re-encode video
#         "-preset", preset,           # Set encoding preset
#         "-crf", str(crf),            # Set CRF for quality
#         "-r", str(fps),              # Set frame rate
#         "-pix_fmt", "yuv420p",       # Set pixel format
#         "-profile:v", "high",        # Set H.264 profile
#         "-an",                        # Disable audio stream
#         segment_file
#     ]
#     print(f"[DEBUG] Extracting segment with command: {' '.join(extract_cmd)}")
#     subprocess.run(extract_cmd, check=True)

#     list_file = os.path.join(OUTPUT_DIR, "segment_list.txt")
#     print(f"[DEBUG] Creating segment list at: {list_file}")
#     with open(list_file, "w") as f:
#         for _ in range(repeat_count):
#             f.write(f"file '{segment_file}'\n")

#     repeated_file = os.path.join(OUTPUT_DIR, "temp_repeated.mp4")
#     concat_cmd = [
#         FFMPEG_PATH, "-y",
#         "-f", "concat",
#         "-safe", "0",
#         "-i", list_file,
#         "-vf", vf_filter,            # Apply scaling and cropping
#         "-c:v", "libx264",           # Re-encode video
#         "-preset", preset,           # Set encoding preset
#         "-crf", str(crf),            # Set CRF for quality
#         "-r", str(fps),              # Set frame rate
#         "-pix_fmt", "yuv420p",       # Set pixel format
#         "-profile:v", "high",        # Set H.264 profile
#         "-an",                        # Disable audio stream
#         repeated_file
#     ]
#     print(f"[DEBUG] Concatenating segments with command: {' '.join(concat_cmd)}")
#     subprocess.run(concat_cmd, check=True)

#     final_cmd = [
#         FFMPEG_PATH, "-y",
#         "-i", repeated_file,
#         "-t", str(desired_duration),
#         "-vf", vf_filter,            # Apply scaling and cropping
#         "-c:v", "libx264",           # Re-encode video
#         "-preset", preset,           # Set encoding preset
#         "-crf", str(crf),            # Set CRF for quality
#         "-r", str(fps),              # Set frame rate
#         "-pix_fmt", "yuv420p",       # Set pixel format
#         "-profile:v", "high",        # Set H.264 profile
#         "-an",                        # Disable audio stream
#         output_video
#     ]
#     print(f"[DEBUG] Trimming final video with command: {' '.join(final_cmd)}")
#     subprocess.run(final_cmd, check=True)

#     # Cleanup temporary files
#     print(f"[DEBUG] Cleaning up temporary files.")
#     os.remove(segment_file)
#     os.remove(list_file)
#     os.remove(repeated_file)


def combine_audio_video(audio_file: str, video_file: str, output_video: str, audio_bitrate: str = "128k"):
    """
    Combine audio and video into a single file using FFmpeg.

    Args:
        audio_file (str): Path to the input audio file.
        video_file (str): Path to the input video file.
        output_video (str): Path to save the combined output video.
        audio_bitrate (str, optional): Bitrate for the audio stream. Defaults to "128k".
    """
    # Ensure that the input files exist
    if not os.path.exists(audio_file):
        logging.error(f"Audio file does not exist: {audio_file}")
        raise FileNotFoundError(f"Audio file not found: {audio_file}")
    if not os.path.exists(video_file):
        logging.error(f"Video file does not exist: {video_file}")
        raise FileNotFoundError(f"Video file not found: {video_file}")

    # Prepare the FFmpeg command
    command = [
        'ffmpeg',
        '-y',  # Overwrite output files without asking
        '-i', video_file,
        '-i', audio_file,
        '-c:v', 'copy',           # Copy the video stream without re-encoding
        '-c:a', 'aac',            # Encode audio to AAC
        '-b:a', audio_bitrate,    # Set audio bitrate
        '-strict', 'experimental',# Allow experimental codecs if necessary
        output_video
    ]

    # Log the command for debugging
    logging.info(f"Running FFmpeg command: {' '.join(command)}")

    try:
        # Run the FFmpeg command and capture output
        process = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        logging.info(f"FFmpeg output: {process.stdout}")
        if process.stderr:
            logging.warning(f"FFmpeg warnings: {process.stderr}")
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg failed to combine audio and video: {e.stderr}")
        raise e