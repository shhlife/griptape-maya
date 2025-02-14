import importlib
import sys

import maya.cmds as cmds


def reload_all_modules():
    """Recursively reload all modules in the griptape_tools package"""

    # Gather all submodules that start with "griptape_tools"
    griptape_modules = [
        module
        for name, module in sys.modules.items()
        if name and name.startswith("griptape_tools") and isinstance(module, type(sys))
    ]

    # Reload in reverse order to avoid dependency issues
    for module in reversed(griptape_modules):
        importlib.reload(module)

    print("All Griptape tools reloaded successfully!")


def rebuild_menu():
    """Rebuild the Griptape menu"""
    if cmds.menu("GriptapeTools", exists=True):
        cmds.deleteUI("GriptapeTools")

    cmds.menu("GriptapeTools", label="Griptape", parent="MayaWindow")

    # Add tools menu items
    cmds.menuItem(
        label="Test Griptape",
        command="import griptape_tools.test_tool as test; test.hello_griptape()",
    )

    # Add reload option at bottom
    cmds.menuItem(divider=True)
    cmds.menuItem(
        label="Reload All Tools",
        command="import griptape_tools.core as core; core.reload_and_rebuild()",
    )


def reload_and_rebuild(*args):
    """Reload all modules and rebuild the menu"""
    reload_all_modules()
    rebuild_menu()
