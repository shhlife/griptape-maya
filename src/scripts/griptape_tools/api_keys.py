import os
import webbrowser
from functools import partial

import maya.cmds as cmds
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class APIKeyManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Dictionary of API keys and their documentation URLs
        self.api_keys = {
            "OPENAI_API_KEY": "https://platform.openai.com/api-keys",
            "GT_CLOUD_API_KEY": "https://cloud.griptape.ai",
            # Add more keys and their URLs here
        }

        self.setWindowTitle("API Key Manager")
        self.setMinimumWidth(500)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Create a widget for each API key
        for key, url in self.api_keys.items():
            row = QHBoxLayout()

            # Label
            label = QLabel(key)
            label.setMinimumWidth(150)
            row.addWidget(label)

            # Input field
            input_field = QLineEdit()
            input_field.setObjectName(key)  # Set object name for later reference
            current_value = os.getenv(key, "")
            input_field.setText(current_value)
            input_field.setEchoMode(QLineEdit.Password)  # Hide the API key
            row.addWidget(input_field)

            # Get Key button
            get_key_btn = QPushButton("Get Key")
            get_key_btn.clicked.connect(partial(self.open_url, url))
            row.addWidget(get_key_btn)

            # Add row to main layout
            main_layout.addLayout(row)

        # Save and Cancel buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_keys)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.close)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        main_layout.addLayout(button_layout)

    def open_url(self, url):
        webbrowser.open(url)

    def save_keys(self):
        # Find Maya's user preferences directory
        maya_app_dir = os.path.expanduser("~/Library/Preferences/Autodesk/maya")
        if not os.path.exists(maya_app_dir):
            maya_app_dir = os.path.expanduser("~/maya")  # Windows fallback

        # Create or update the env file
        env_file = os.path.join(maya_app_dir, "env_vars.env")

        with open(env_file, "w") as f:
            for key in self.api_keys.keys():
                input_field = self.findChild(QLineEdit, key)
                if input_field and input_field.text():
                    f.write(f"{key}={input_field.text()}\n")
                    os.environ[key] = input_field.text()

        self.close()
        cmds.confirmDialog(
            title="Success", message="API keys saved successfully!", button=["OK"]
        )


def show_api_key_manager():
    global dialog
    try:
        dialog.close()
        dialog.deleteLater()
    except Exception as e:
        print(e)
        pass

    dialog = APIKeyManager()
    dialog.show()


if __name__ == "__main__":
    show_api_key_manager()
