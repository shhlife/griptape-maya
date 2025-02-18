from __future__ import annotations

import base64
import collections
import io
import logging
import queue
import threading
import wave
from collections.abc import Iterator

import attrs
import pyaudio
import webrtcvad
from griptape.artifacts import AudioArtifact
from griptape.configs import Defaults
from griptape.configs.logging import JsonFormatter
from griptape.drivers import OpenAiChatPromptDriver
from griptape.events import AudioChunkEvent
from griptape.structures import Agent

# Configure the logger for the "griptape" namespace

logger = logging.getLogger(Defaults.logging_config.logger_name)
logger.setLevel(logging.INFO)
logger.handlers[0].setFormatter(JsonFormatter())


@attrs.define
class AudioStream:
    """An audio stream class that detects speech segments and yields audio bytes."""

    format: int = attrs.field(default=pyaudio.paInt16)
    channels: int = attrs.field(default=1)
    rate: int = attrs.field(default=16000)
    chunk_size: int = attrs.field(default=1024)
    vad_mode: int = attrs.field(default=3)
    frame_duration_ms: int = attrs.field(default=30)
    padding_duration_ms: int = attrs.field(default=300)
    stream: pyaudio.Stream = attrs.field(init=False, default=None)
    vad: webrtcvad.Vad = attrs.field(init=False, default=None)
    audio: pyaudio.PyAudio = attrs.field(init=False, default=None)

    def __attrs_post_init__(self) -> None:
        """Initialize the audio stream and WebRTC VAD."""
        try:
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk_size,
            )
            self.vad = webrtcvad.Vad()
            self.vad.set_mode(self.vad_mode)
            logger.debug("Audio stream and VAD initialized successfully.")
        except Exception as e:
            logger.error("Failed to initialize VAD: %s", e)
            raise

    def is_speech(self, frame: bytes) -> bool:
        """Check if the given audio frame contains speech."""
        try:
            return self.vad.is_speech(frame, self.rate)
        except ValueError as e:
            logger.error("Invalid input to VAD: %s", e)
            return False

    def run(self) -> Iterator[AudioArtifact]:
        logger.info("Ready to go...")
        num_padding_frames = int(self.padding_duration_ms / self.frame_duration_ms)
        ring_buffer = collections.deque(maxlen=num_padding_frames)
        triggered = False
        voiced_frames = []

        try:
            while True:
                # Read audio data from the stream
                frame_size = int(self.rate * self.frame_duration_ms / 1000.0)
                frame = self.stream.read(frame_size, exception_on_overflow=False)

                # Check if the frame contains speech
                is_speech = self.is_speech(frame)
                ring_buffer.append((frame, is_speech))

                if not triggered:
                    num_voiced = len([f for f, speech in ring_buffer if speech])
                    if ring_buffer.maxlen and num_voiced > 0.9 * ring_buffer.maxlen:
                        triggered = True
                        logger.debug("Speech detected, starting collection...")
                        for f, _ in ring_buffer:
                            voiced_frames.append(f)
                        ring_buffer.clear()
                else:
                    voiced_frames.append(frame)
                    num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                    if ring_buffer.maxlen and num_unvoiced > 0.9 * ring_buffer.maxlen:
                        logger.debug("Silence detected, yielding speech segment...")
                        triggered = False
                        # Yield the collected audio frames as a WAV file
                        yield self._frames_to_audio_artifact(voiced_frames)
                        ring_buffer.clear()
                        voiced_frames = []

        except KeyboardInterrupt:
            logger.info("Stopped by user.")
        except Exception as e:
            logger.error("Error during audio stream: %s", e)
        finally:
            self.close()

    def _frames_to_audio_artifact(self, frames: list[bytes]) -> AudioArtifact:
        """Convert audio frames to a WAV AudioArtifact."""
        audio_data = b"".join(frames)
        with io.BytesIO() as wav_buffer:
            with wave.open(wav_buffer, "wb") as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(self.audio.get_sample_size(self.format))
                wav_file.setframerate(self.rate)
                wav_file.writeframes(audio_data)
            wav_bytes = wav_buffer.getvalue()
        return AudioArtifact(wav_bytes, format="wav")

    def close(self) -> None:
        """Close the audio stream and terminate resources."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()
        logger.debug("Audio stream closed successfully.")


@attrs.define
class AudioPlayer:
    """An audio player class that plays audio from a queue."""

    format: int = attrs.field(default=pyaudio.paInt16)
    channels: int = attrs.field(default=1)
    rate: int = attrs.field(default=24000)
    chunk_size: int = attrs.field(default=1024)
    audio_queue: queue.Queue = attrs.field(default=queue.Queue())

    audio: pyaudio.PyAudio = attrs.field(init=False, default=None)
    stream: pyaudio.Stream = attrs.field(init=False, default=None)
    thread: threading.Thread = attrs.field(init=False, default=None)

    def __attrs_post_init__(self) -> None:
        """Initialize the audio player."""
        try:
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                output=True,
                frames_per_buffer=self.chunk_size,
            )
            logger.debug("Audio player initialized successfully.")
        except Exception as e:
            logger.error("Failed to initialize audio player: %s", e)
            raise

    def __enter__(self) -> AudioPlayer:
        self.thread = threading.Thread(target=self._play_audio_from_queue, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def _play_audio_from_queue(self) -> None:
        """Continuously play audio from the queue."""
        try:
            while True:
                audio_bytes = self.audio_queue.get()
                for i in range(0, len(audio_bytes), self.chunk_size):
                    chunk = audio_bytes[i : i + self.chunk_size]
                    self.stream.write(chunk)
        except Exception as e:
            logger.error("Playback error: %s", e)

    def close(self) -> None:
        """Close the audio player and terminate resources."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()
        self.thread.join()
        logger.info("Audio player closed successfully.")


def start_recording():
    agent = Agent(prompt_driver=OpenAiChatPromptDriver(model="gpt-4o-audio-preview"))
    with AudioPlayer() as audio_player:
        for audio_artifact in AudioStream().run():
            for event in agent.run_stream(audio_artifact):
                if isinstance(event, AudioChunkEvent):
                    audio_player.audio_queue.put(base64.b64decode(event.data))


if __name__ == "__main__":
    if False:
        stream = AudioStream()
        for artifact in stream.run():
            print("Captured:", artifact.value)
            break  # Just capture one chunk
        stream.close()

    else:
        agent = Agent(
            prompt_driver=OpenAiChatPromptDriver(model="gpt-4o-audio-preview")
        )
        with AudioPlayer() as audio_player:
            for audio_artifact in AudioStream().run():
                for event in agent.run_stream(audio_artifact):
                    if isinstance(event, AudioChunkEvent):
                        print(event.data)
                        audio_player.audio_queue.put(base64.b64decode(event.data))
