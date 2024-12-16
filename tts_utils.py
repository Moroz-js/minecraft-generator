# tts_utils.py
import os
import asyncio
from typing import Optional

import edge_tts # type: ignore
from pydub import AudioSegment # type: ignore
from constants import AUDIO_DIR


async def synthesize_speech_async(text: str, output_file: str, voice: Optional[str] = "en-US-AndrewMultilingualNeural") -> float:
    """
    Asynchronously synthesize speech from text and save it as an MP3 file using edge-tts.

    Args:
        text (str): The text to synthesize.
        output_file (str): Path to save the audio file.
        voice (str, optional): The voice to use for synthesis. Defaults to "en-US-JennyNeural".

    Returns:
        float: Duration of the synthesized speech in seconds.
    """
    try:
        # Initialize the communicator with the desired voice
        communicate = edge_tts.Communicate(text, voice)
        
        # Save the synthesized speech to the output file
        await communicate.save(output_file)
        
        # Load the audio file to determine its duration
        audio = AudioSegment.from_file(output_file)
        new_sample_rate = int(audio.frame_rate * 1.1)
        sped_up_audio = audio._spawn(audio.raw_data, overrides={'frame_rate': new_sample_rate}).set_frame_rate(audio.frame_rate)
        
        # Export the sped-up audio to the same output file or a different one
        sped_up_audio.export(output_file, format="mp3")
        
        # Return the duration of the sped-up audio
        duration = sped_up_audio.duration_seconds
        
        return duration
    except Exception as e:
        print(f"An error occurred during synthesis: {e}")
        return 0.0

def synthesize_speech(text: str, output_file: str, voice: Optional[str] = "en-US-AndrewMultilingualNeural") -> float:
    """
    Synthesize speech from text and save it as an MP3 file using edge-tts.

    Args:
        text (str): The text to synthesize.
        output_file (str): Path to save the audio file.
        voice (str, optional): The voice to use for synthesis. Defaults to "en-US-JennyNeural".

    Returns:
        float: Duration of the synthesized speech in seconds.
    """
    os.makedirs(AUDIO_DIR, exist_ok=True)
    output_path = os.path.join(AUDIO_DIR, output_file)
    
    # Run the asynchronous synthesis
    duration = asyncio.run(synthesize_speech_async(text, output_path, voice))
    
    return duration