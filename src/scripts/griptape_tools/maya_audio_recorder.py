import os
import threading
import wave

import maya.cmds as cmds
import numpy as np
import sounddevice as sd

# Settings
SAMPLE_RATE = 44100  # CD-quality audio
CHANNELS = 1
FILENAME = os.path.join(cmds.internalVar(userAppDir=True), "maya_audio_recording.wav")

# Global Variables
recording = False
audio_data = []


def callback(indata, frames, time, status):
    """Callback function to store audio data"""
    if status:
        print(status)
    if recording:
        audio_data.append(indata.copy())


def start_recording():
    """Starts recording audio"""
    global recording, audio_data
    if recording:
        cmds.warning("Already recording!")
        return
    recording = True
    audio_data = []
    threading.Thread(target=record_thread, daemon=True).start()
    cmds.warning("Recording started...")


def record_thread():
    """Recording thread function"""
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, callback=callback):
        while recording:
            sd.sleep(100)


def stop_recording():
    """Stops recording and saves the audio file"""
    global recording
    if not recording:
        cmds.warning("Not currently recording!")
        return
    recording = False
    cmds.warning("Recording stopped, saving file...")

    # Convert recorded data to a single numpy array
    audio_np = np.concatenate(audio_data, axis=0)

    # Save as a WAV file
    with wave.open(FILENAME, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes((audio_np * 32767).astype(np.int16).tobytes())

    cmds.warning(f"Audio saved to: {FILENAME}")
