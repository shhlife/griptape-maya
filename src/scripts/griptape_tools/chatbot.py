import threading

import maya.cmds as cmds
import maya.utils
from griptape.structures import Agent
from griptape.utils import Stream
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QTextCursor  # Added QTextCursor import
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTextEdit, QVBoxLayout, QWidget


class ChatbotUI(QWidget):
    update_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Griptape Chat")
        self.resize(800, 600)
        self.agent = Agent(stream=True)

        self.setup_ui()
        self.update_signal.connect(self.update_chat)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Chat history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        layout.addWidget(self.chat_history)

        # Input area
        input_layout = QHBoxLayout()

        self.input_field = QTextEdit()
        self.input_field.setMaximumHeight(100)
        self.input_field.setPlaceholderText("Message Griptape...")
        self.input_field.installEventFilter(self)
        input_layout.addWidget(self.input_field)

        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)

        layout.addLayout(input_layout)

    def eventFilter(self, obj, event):
        if obj == self.input_field and event.type() == QKeyEvent.KeyPress:
            if (
                event.key() == Qt.Key_Return
                and not event.modifiers() & Qt.ShiftModifier
            ):
                self.send_message()
                return True
        return super().eventFilter(obj, event)

    def send_message(self):
        message = self.input_field.toPlainText().strip()
        if not message:
            return

        self.input_field.clear()
        self.chat_history.append(f"You: {message}\n")

        threading.Thread(target=self.generate_response, args=(message,)).start()

    def generate_response(self, message):
        try:
            self.chat_history.append("Assistant: ")
            for chunk in Stream(self.agent).run(message):
                if chunk and chunk.value:
                    maya.utils.executeInMainThreadWithResult(
                        self.update_signal.emit, chunk.value
                    )
        except Exception as e:
            cmds.warning(f"Error generating response: {str(e)}")

    def update_chat(self, text):
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.End)  # Fixed: using QTextCursor.End
        cursor.insertText(text)
        self.chat_history.setTextCursor(cursor)


def show_chatbot():
    global chatbot_window
    try:
        chatbot_window.close()
        chatbot_window.deleteLater()
    except:
        pass

    chatbot_window = ChatbotUI()
    chatbot_window.show()
