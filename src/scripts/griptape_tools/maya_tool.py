from __future__ import annotations

import re

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
                        description="Maya python command to execute. Examples: ls(sl=1), polyCube(), polySphere(radius=2), createNode( 'transform', n='transform1' ) ",
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
            result = eval(f"mc.{command_str}")
            return TextArtifact(str(result))
        except Exception as e:
            return ErrorArtifact(str(e))
