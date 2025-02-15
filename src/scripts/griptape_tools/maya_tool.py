from __future__ import annotations

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
            f.write("import maya\nimport maya.cmds as cmds\n")
            f.write("results = []\n")
            for command in command_list:
                # if command has True or False, convert it to boolean
                f.write(
                    f"results.append(maya.utils.executeInMainThreadWithResult(lambda: {command}))\n"
                )

            f.write("print(results)")
        print(f"Saved to {input_file}")

        # Create a namespace
        namespace = {}

        try:
            with open(input_file) as script_file:
                exec(script_file.read(), namespace)

            result = namespace.get("results")

            return TextArtifact(str(result))
        except Exception as e:
            return ErrorArtifact(str(e))
