from __future__ import annotations

import re

import maya.cmds as mc
from attr import define
from griptape.artifacts import ErrorArtifact, TextArtifact
from griptape.tools import BaseTool
from griptape.utils.decorators import activity
from schema import Literal, Schema


def parse_parameters(param_str: str) -> dict:
    """Safely parses a parameter string into a dictionary."""
    try:
        param_str = param_str.strip()
        if not param_str:
            return {}

        params = {}

        # ✅ Regex to find key=value pairs (handles quotes & spaces correctly)
        param_pairs = re.findall(r"(\w+)\s*=\s*(['\"]?.+?['\"]?)(?:,|$)", param_str)

        for key, value in param_pairs:
            key = key.strip()

            # ✅ Convert booleans
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            # ✅ Convert numbers
            elif value.replace(".", "", 1).isdigit():
                value = float(value) if "." in value else int(value)
            else:
                # ✅ Strip quotes from strings
                value = value.strip("'\"")

            params[key] = value

        return params

    except Exception as e:
        print(f"Error parsing parameters: {e}")
        return {}


@define
class MayaTool(BaseTool):
    @activity(
        config={
            "description": "Can be used to execute python commands in Maya",
            "schema": Schema(
                {
                    Literal(
                        "command_str",
                        description="Maya python command to execute. Examples: ls(sl=True), polyCube(), polySphere(radius=2), createNode( 'transform', n='transform1' ) ",
                    ): str,
                }
            ),
        }
    )
    def cmd(self, params: dict) -> TextArtifact | ErrorArtifact:
        command_str = params["values"].get("command_str")
        try:
            print(f"Executing: {command_str}")

            # ✅ Split at the first "(" to separate command and parameters
            cmd_split = command_str.split("(", 1)

            if len(cmd_split) != 2:
                return ErrorArtifact(f"Invalid command format: {command_str}")

            cmd_name = cmd_split[0].strip()  # Extract the Maya command name
            args_str = (
                cmd_split[1].rstrip(")").strip()
            )  # Extract arguments without trailing ")"

            # ✅ Check if the Maya command exists
            if not hasattr(mc, cmd_name):
                return ErrorArtifact(f"Invalid Maya command: {cmd_name}")

            cmd = getattr(mc, cmd_name)  # Get the Maya function

            # ✅ Parse arguments safely
            print(f"Parsing arguments: {args_str}")
            kwargs = parse_parameters(args_str)

            # ✅ Debugging: Check the actual types before calling Maya
            print(f"Executing: {cmd_name}({kwargs})")
            print(f"Types: { {k: type(v) for k, v in kwargs.items()} }")

            result = cmd(**kwargs) if kwargs else cmd()
            print(result)
            return TextArtifact(str(result))
        except Exception as e:
            return ErrorArtifact(str(e))
