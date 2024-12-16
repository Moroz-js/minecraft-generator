import moviepy.editor as mp
import speech_recognition as sr
import os
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.editor import TextClip

def auto_caption(input_video: str):
    print("Starting captioning process...")
    
    # Load the video
    video = mp.VideoFileClip(input_video)
    print(f"Video loaded: {input_video}")
    
    # Extract audio from the video
    audio = video.audio
    audio_file = "temp_audio.wav"
    audio.write_audiofile(audio_file)
    print(f"Audio extracted and saved as {audio_file}")
    
    # Use SpeechRecognition to transcribe the audio to text
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
    
    # Perform speech-to-text transcription
    try:
        transcript = recognizer.recognize_google(audio_data)
        print(f"Transcription completed: {transcript[:100]}...")  # Print first 100 chars for brevity
    except sr.UnknownValueError:
        print("Audio is unintelligible, skipping subtitle generation.")
        return video
    except sr.RequestError:
        print("Speech Recognition service is unavailable, skipping subtitle generation.")
        return video
    
    # Split the transcript into chunks of 1-3 words for "quick" captions
    words = transcript.split()
    chunk_size = 3  # Each subtitle will contain up to 3 words
    subtitles = []
    
    print(f"Total words in transcript: {len(words)}")
    
    # Split words into chunks and assign each chunk a small time interval
    chunk_duration = video.duration / len(words)  # Approximate time for each word
    start_time = 0

    # Group words into chunks and compute start and end times
    for i in range(0, len(words), chunk_size):
        # Avoid exceeding the list length by using min(chunk_size, len(words) - i)
        end_time = start_time + chunk_duration * min(chunk_size, len(words) - i)  
        subtitle_text = ' '.join(words[i:i + chunk_size])
        
        # Append (start_time, subtitle_text) to subtitles list
        subtitles.append((start_time, subtitle_text))
        print(f"Added subtitle: ({start_time}, {subtitle_text})")
        
        start_time = end_time  # Update start time for next chunk
    
    # Debugging: Print out the subtitles to check their format
    print("Subtitles list:")
    for subtitle in subtitles:
        print(subtitle)  # Should print a tuple of (start_time, subtitle_text)
    
    # Create a function to make text clips for each subtitle
    def make_textclip(txt):
        print(f"Creating text clip for subtitle: {txt}")
        return TextClip(
            txt,
            fontsize=48,  # Set font size to 48
            color='white',  # Set text color to white
            font='Montserrat-Bold',  # Set font to Montserrat Bold
            align='center',  # Center-align the text
            stroke_width=3,  # Set the border width
            stroke_color='black',  # Set border color to black
            method='caption'  # Use caption method for better text wrapping
        ).set_duration(chunk_duration * chunk_size).set_pos('center')  # Position in the center and set duration
    
    # Create the subtitle clip
    try:
        subtitle_clip = SubtitlesClip(subtitles, make_textclip)
        print("Subtitle clip created successfully.")
    except Exception as e:
        print(f"Error creating subtitle clip: {e}")
        return video
    
    # Overlay subtitles onto the video
    try:
        video_with_subtitles = mp.CompositeVideoClip([video, subtitle_clip.set_pos('bottom')])
        print("Video with subtitles created successfully.")
    except Exception as e:
        print(f"Error overlaying subtitles: {e}")
        return video
    
    # Output file path
    output_file = os.path.splitext(input_video)[0] + "_with_subtitles.mp4"
    
    # Write the result to a file
    try:
        video_with_subtitles.write_videofile(output_file, codec="libx264", fps=video.fps)
        print(f"Video with subtitles saved to {output_file}")
    except Exception as e:
        print(f"Error writing video to file: {e}")
        return video
    
    # Clean up temporary audio file
    os.remove(audio_file)
    
    return output_file

