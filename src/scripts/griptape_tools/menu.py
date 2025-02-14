# src/scripts/griptape_tools/menu.py
import importlib

import maya.cmds as cmds
from griptape_tools.api_keys import show_api_key_manager


def create_menu():
    """Create the Griptape menu in Maya"""
    rebuild_menu()


def rebuild_menu():
    """Rebuild the Griptape menu from scratch"""
    # Delete existing menu if it exists
    if cmds.menu("GriptapeTools", exists=True):
        cmds.deleteUI("GriptapeTools")

    # Create menu
    griptape_menu = cmds.menu("GriptapeTools", label="Griptape", parent="MayaWindow")

    # Add menu items
    cmds.menuItem(label="API Key Manager", command=lambda x: show_api_key_manager())

    # Add separator
    cmds.menuItem(divider=True)

    # Add reload option at bottom
    cmds.menuItem(label="Reload Tools", command=reload_tools)


def reload_tools(*args):
    """Reload all Griptape tools and rebuild menu"""
    try:
        import griptape_tools

        importlib.reload(griptape_tools)
        rebuild_menu()
        print("Griptape tools reloaded successfully!")
    except Exception as e:
        cmds.warning(f"Failed to reload Griptape tools: {e}")
