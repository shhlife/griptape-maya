import threading

import maya.cmds as cmds
import maya.OpenMayaUI as omui
import maya.utils
from griptape.structures import Agent
from griptape.utils import Stream
from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QDockWidget,
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


class ChatbotUI(QWidget):
    update_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Griptape Chat")
        self.agent = Agent(stream=True)

        self.setup_ui()
        self.update_signal.connect(self.update_chat)

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
        message = self.input_field.toPlainText().strip()
        if not message:
            return

        self.input_field.clear()

        # Ensures user messages start on a new line
        self.append_chat(f"You: {message}", "#FFD700", newline=True)

        threading.Thread(target=self.generate_response, args=(message,)).start()

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
    global chatbot_dock

    # If the dock already exists, delete it
    if cmds.workspaceControl("ChatbotDock", q=True, exists=True):
        cmds.deleteUI("ChatbotDock")

    # Create the workspace control
    cmds.workspaceControl(
        "ChatbotDock", label="Griptape Chat", dockToMainWindow=["right", 1]
    )

    # Retrieve the workspace control widget
    workspace_control_ptr = omui.MQtUtil.findControl("ChatbotDock")
    if not workspace_control_ptr:
        cmds.warning("Failed to find workspace control.")
        return

    workspace_control_widget = wrapInstance(int(workspace_control_ptr), QMainWindow)

    # Create and set up the chatbot UI
    chatbot_dock = QDockWidget("Griptape Chat", parent=workspace_control_widget)
    chatbot_dock.setObjectName("ChatbotDockWidget")
    chatbot_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

    chatbot_ui = ChatbotUI()  # Make sure the chatbot UI is instantiated
    chatbot_dock.setWidget(chatbot_ui)

    # Make sure the chatbot UI is visible
    chatbot_dock.show()
    workspace_control_widget.layout().addWidget(chatbot_dock)
