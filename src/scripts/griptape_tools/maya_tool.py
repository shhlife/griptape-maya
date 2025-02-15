from __future__ import annotations

import maya
import maya.cmds as cmds
from attr import define
from griptape.artifacts import ErrorArtifact, TextArtifact
from griptape.tools import BaseTool
from griptape.utils.decorators import activity
from schema import Literal, Schema


@define
class MayaTool(BaseTool):
    @activity(
        config={
            "description": "Can be used to execute python commands in Maya",
            "schema": Schema(
                {
                    Literal(
                        "command_list",
                        description="Python commands to execute. If using a Maya command, preface it with `cmds`. Examples: ['cmds.ls(sl=1)', 'cmds.polyCube()', 'cmds.polySphere(radius=2)']",
                    ): list[str],
                }
            ),
        }
    )
    def cmd(self, params: dict) -> TextArtifact | ErrorArtifact:
        command_list = params["values"].get("command_list", [])
        print(f"Executing: {command_list}")

        # save the results to a temporary file
        input_file = "/var/tmp/test.py"

        with open(input_file, "w") as f:
            f.write("import maya.cmds as cmds\n")
            f.write("results = []\n")
            for command in command_list:
                # if command starts with cmds, then it's a maya command and add it to the results
                # But the command may be indented, so we'll need to strip it, then add the spacing back
                # with results.append(command)
                if command.strip().startswith("cmds."):
                    # get the spacing that was there in front of the command
                    spacing = command.split("cmds.")[0]
                    f.write(f"{spacing}results.append({command})\n")
                else:
                    f.write(f"{command}\n")

            # f.write("print(results)")
        print(f"Saved to {input_file}")

        # Create a namespace
        namespace = {}
        try:
            with open(input_file) as script_file:
                script_code = script_file.read()
                # start undo chunk
                cmds.undoInfo(openChunk=True)
                maya.utils.executeInMainThreadWithResult(
                    lambda: exec(script_code, namespace)
                )
                cmds.undoInfo(closeChunk=True)

            # Print results
            # print(f"Script Execution Completed. Namespace: {namespace}")
            return TextArtifact(str(namespace["results"]))
        except Exception as e:
            print(f"Execution Error: {e}")
