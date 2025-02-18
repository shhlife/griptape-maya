# audio_recorder.py
import time

import sounddevice as sd
import soundfile as sf


def record_audio(duration=5):
    # Audio parameters
    sample_rate = 44100
    channels = 1

    # Record audio
    recording = sd.rec(
        int(duration * sample_rate), samplerate=sample_rate, channels=channels
    )

    sd.wait()

    # Generate filename
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"recording_{timestamp}.wav"

    # Save the recording
    sf.write(filename, recording, sample_rate)
    print("RECORDING_SAVED:" + filename)  # Special marker for the Maya script


if __name__ == "__main__":
    record_audio()
