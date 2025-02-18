import tempfile
import threading
import wave

import maya.cmds as cmds
import maya.OpenMayaUI as omui
import maya.utils
import pyaudio
from griptape.drivers.prompt.openai import OpenAiChatPromptDriver
from griptape.loaders import AudioLoader
from griptape.structures import Agent
from griptape.utils import Stream
from pydub import AudioSegment
from pydub.utils import which
from PySide6.QtCore import QEvent, Qt, QTimer, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from shiboken6 import wrapInstance

from .maya_tool import MayaTool


class ChatbotUI(QWidget):
    update_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Griptape Chat")
        self.text_prompt_driver = OpenAiChatPromptDriver(model="gpt-4o", stream=True)
        self.audio_prompt_driver = OpenAiChatPromptDriver(
            model="gpt-4o-audio-preview", stream=True
        )
        self.agent = Agent(
            prompt_driver=self.audio_prompt_driver,
            tools=[MayaTool()],
            stream=True,
        )
        self.temp_path = tempfile.gettempdir()
        self.audio_file_wav = f"{self.temp_path}/recorded_audio.wav"
        self.audio_artifact = None
        self.is_listening = False
        self.listening_thread = None

        self.setup_ui()
        self.update_signal.connect(self.update_chat)

        # 🚀 Set focus on the input field when the UI opens
        self.input_field.setFocus()
        # Ensure ffmpeg is found
        AudioSegment.converter = which("ffmpeg")

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Chat history (forces full width)
        self.chat_history = QTextBrowser()
        self.chat_history.setReadOnly(True)
        self.chat_history.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )  # Allow full width
        self.chat_history.setStyleSheet("""
            QTextBrowser {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #333;
                padding: 5px;
                font-size: 12px;
                word-wrap: normal;  /* Prevent aggressive wrapping */
                white-space: pre-wrap;  /* Preserve formatting but allow wrapping */
                width: 100%;
            }
        """)
        layout.addWidget(self.chat_history)

        # Input area
        input_layout = QHBoxLayout()
        self.input_field = QTextEdit()
        self.input_field.setMaximumHeight(80)
        self.input_field.setPlaceholderText("Message Griptape...")
        self.input_field.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )  # Allow input to expand
        self.input_field.setStyleSheet("""
            QTextEdit {
                background-color: #292929;
                color: #FFFFFF;
                border: 1px solid #444;
                padding: 5px;
                font-size: 12px;
            }
        """)
        self.input_field.installEventFilter(self)
        input_layout.addWidget(self.input_field)

        send_button = QPushButton("Send")
        send_button.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Fixed
        )  # Keep button fixed size
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: #FFF;
                border: 1px solid #666;
                padding: 5px 15px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #666;
            }
        """)
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        # 🎤 Add voice mode button
        self.voice_button = QPushButton("🎤")
        self.voice_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.voice_button.setCheckable(True)
        self.voice_button.clicked.connect(self.toggle_voice_mode)
        input_layout.addWidget(self.voice_button)

        layout.addLayout(input_layout)

    def eventFilter(self, obj, event):
        if obj == self.input_field and event.type() == QEvent.KeyPress:
            if (
                event.key() == Qt.Key_Return
                and not event.modifiers() & Qt.ShiftModifier
            ):
                self.send_message()
                return True
        return super().eventFilter(obj, event)

    def send_message(self):
        message_str = self.input_field.toPlainText().strip()
        if not message_str and not self.audio_artifact:
            return

        message = (message_str, self.audio_artifact)
        self.input_field.clear()
        # Ensures user messages start on a new line
        self.append_chat(f"You: {message_str}", "#FFD700", newline=True)

        threading.Thread(target=self.generate_response, args=(message,)).start()

        self.audio_artifact = None

    def toggle_voice_mode(self):
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()

    def start_listening(self):
        self.is_listening = True
        self.voice_button.setText("⏹️ Stop")
        self.listening_thread = threading.Thread(target=self.record_audio, daemon=True)
        self.append_chat("Recording started...", "#87CEFA")

        self.listening_thread.start()

    def stop_listening(self):
        self.is_listening = False
        self.voice_button.setText("🎤 Record")
        if self.listening_thread and self.listening_thread.is_alive():
            self.listening_thread.join(timeout=1)
        self.append_chat("Recording stopped. Processing audio...", "#87CEFA")
        QTimer.singleShot(0, self.process_audio)

    def record_audio(self):
        """Capture microphone audio and save as a WAV file."""
        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=48000,
            input=True,
            frames_per_buffer=1024,
        )

        frames = []
        print("Recording started...")
        while self.is_listening:
            data = stream.read(1024, exception_on_overflow=False)
            frames.append(data)

        print("Saving recorded audio...")
        stream.stop_stream()
        stream.close()
        pa.terminate()

        with wave.open(self.audio_file_wav, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
            wf.setframerate(48000)
            wf.writeframes(b"".join(frames))

        print(f"Audio saved to {self.audio_file_wav}")
        QTimer.singleShot(
            0, lambda: self.append_chat("Audio recorded successfully.", "#87CEFA")
        )

    def process_audio(self):
        """Process recorded audio and send to LLM."""
        try:
            self.audio_artifact = AudioLoader().load(self.audio_file_wav)
            self.send_message()
        except Exception as e:
            cmds.warning(f"Error processing audio: {str(e)}")

    def append_to_last_chat(self, text):
        """Appends text to the last Assistant message without creating new lines."""
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.End)  # Move to the end of the text
        cursor.insertText(text)  # Append new text at the end
        self.chat_history.setTextCursor(cursor)

    def generate_response(self, message):
        try:
            maya.utils.executeInMainThreadWithResult(
                self.append_chat, "<br>Assistant: ", "#87CEFA"
            )

            for chunk in Stream(self.agent).run(message):
                if chunk and chunk.value:
                    maya.utils.executeInMainThreadWithResult(
                        self.append_to_last_chat, chunk.value
                    )
            maya.utils.executeInMainThreadWithResult(self.append_to_last_chat, "\n")

        except Exception as e:
            cmds.warning(f"Error generating response: {str(e)}")

    def update_chat(self, text):
        self.append_chat(text, "#FFFFFF")

    def append_chat(self, text, color, newline=True):
        """Appends a new message to the chat with optional newline formatting."""
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.End)

        if newline:
            text = f"<br>{text}"  # Adds a line break before the new message

        cursor.insertHtml(f'<span style="color: {color};">{text}</span>')
        self.chat_history.setTextCursor(cursor)
        self.chat_history.verticalScrollBar().setValue(
            self.chat_history.verticalScrollBar().maximum()
        )


def get_maya_main_window():
    """Returns the Maya main window as a PySide6 QMainWindow instance."""
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QMainWindow)


def show_chatbot():
    # If the dock already exists, just show it and force correct size
    if cmds.workspaceControl("ChatbotDock", q=True, exists=True):
        cmds.workspaceControl("ChatbotDock", e=True, visible=True)
        cmds.control("ChatbotDock", e=True, visible=True)
        cmds.workspaceControl(
            "ChatbotDock", e=True, height=500, width=400
        )  # 🚀 Ensure correct initial size
        cmds.refresh()
        return  # ✅ Exit early if the UI already exists

    # Create the workspace control
    cmds.workspaceControl(
        "ChatbotDock",
        label="Griptape Chat",
        dockToMainWindow=["right", 1],
        retain=False,
    )

    # Get the workspace control as a QWidget
    workspace_control_ptr = omui.MQtUtil.findControl("ChatbotDock")
    if not workspace_control_ptr:
        cmds.warning("Failed to find workspace control.")
        return

    workspace_control_widget = wrapInstance(int(workspace_control_ptr), QWidget)

    # ✅ Make sure workspace control has a layout
    if not workspace_control_widget.layout():
        workspace_control_widget.setLayout(QVBoxLayout())

    # ✅ Create the chatbot UI and make it **expand** fully
    chatbot_ui = ChatbotUI(parent=workspace_control_widget)
    chatbot_ui.setSizePolicy(
        QSizePolicy.Expanding, QSizePolicy.Expanding
    )  # 🚀 Allow full expansion
    workspace_control_widget.layout().addWidget(chatbot_ui)

    chatbot_ui.show()

    # 🔥 Ensure it appears with correct size
    cmds.workspaceControl("ChatbotDock", e=True, visible=True)
    cmds.control("ChatbotDock", e=True, visible=True)
    cmds.workspaceControl(
        "ChatbotDock", e=True, height=500, width=400
    )  # 🚀 Force correct size
    cmds.refresh()
