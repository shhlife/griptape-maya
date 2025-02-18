import os
import subprocess
import sys
from pathlib import Path

import maya.cmds as cmds


class MayaAudioRecorder:
    def __init__(self):
        self.recording_process = None
        self.script_dir = str(Path(__file__).parent.absolute())
        self.recorder_script = os.path.join(self.script_dir, "audio_recorder.py")
        self.create_ui()

    def create_ui(self):
        if cmds.window("audioRecorderWindow", exists=True):
            cmds.deleteUI("audioRecorderWindow")

        window = cmds.window(
            "audioRecorderWindow", title="Maya Audio Recorder", width=300
        )
        main_layout = cmds.columnLayout(adjustableColumn=True)

        # Add buttons
        cmds.separator(height=10, style="none")
        cmds.button(label="Record (5 seconds)", command=self.start_recording)

        cmds.separator(height=10, style="none")
        self.status_text = cmds.text(label="Status: Ready", align="center")

        cmds.showWindow(window)

    def start_recording(self, *args):
        try:
            # Get system's Python path
            if sys.platform == "darwin":  # macOS
                python_path = (
                    "/Users/jason/Documents/GitHub/griptape-maya/.venv/bin/python"
                )
            else:  # Windows
                python_path = "python"

            # Start recording process
            self.recording_process = subprocess.Popen(
                [python_path, self.recorder_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            cmds.text(self.status_text, edit=True, label="Status: Recording...")

            # Wait for the recording to complete
            output, error = self.recording_process.communicate()

            if error:
                print("Error:", error)
                cmds.text(self.status_text, edit=True, label="Status: Recording failed")
                return

            # Look for the filename in the output
            for line in output.split("\n"):
                if line.startswith("RECORDING_SAVED:"):
                    filename = line.split(":", 1)[1]
                    # Move file to Maya project
                    maya_project_path = cmds.workspace(query=True, rootDirectory=True)
                    sound_dir = os.path.join(maya_project_path, "sound")

                    if not os.path.exists(sound_dir):
                        os.makedirs(sound_dir)

                    # Move the file
                    if os.path.exists(filename):
                        new_path = os.path.join(sound_dir, os.path.basename(filename))
                        os.rename(filename, new_path)
                        cmds.text(
                            self.status_text,
                            edit=True,
                            label=f"Status: Saved to {os.path.basename(filename)}",
                        )
                    break

        except Exception as e:
            error_msg = f"Failed to record: {str(e)}"
            cmds.text(self.status_text, edit=True, label=error_msg)
            print(error_msg)


def create_audio_recorder():
    return MayaAudioRecorder()
