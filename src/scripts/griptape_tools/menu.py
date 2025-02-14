# src/scripts/griptape_tools/menu.py
import importlib
import pkgutil
import sys

import maya.cmds as cmds
from griptape_tools.api_keys import show_api_key_manager
from griptape_tools.chatbot import show_chatbot


def create_menu():
    """Create the Griptape menu in Maya"""
    rebuild_menu()


def rebuild_menu():
    """Rebuild the Griptape menu from scratch"""
    if cmds.menu("GriptapeTools", exists=True):
        cmds.deleteUI("GriptapeTools")

    griptape_menu = cmds.menu("GriptapeTools", label="Griptape", parent="MayaWindow")

    cmds.menuItem(label="API Key Manager", command=lambda x: show_api_key_manager())
    cmds.menuItem(label="Chatbot", command=lambda x: show_chatbot())

    cmds.menuItem(divider=True)
    cmds.menuItem(label="Reload Tools", command=reload_tools)


def reload_tools(*args):
    """Reload all Griptape tools and rebuild menu"""
    try:
        import griptape_tools

        # Get all submodules recursively
        def get_all_submodules(package):
            modules = []
            for importer, modname, ispkg in pkgutil.walk_packages(package.__path__):
                full_name = f"{package.__name__}.{modname}"
                if full_name in sys.modules:
                    modules.append(sys.modules[full_name])
                    if ispkg:  # If it's a package, get its submodules too
                        modules.extend(get_all_submodules(sys.modules[full_name]))
            return modules

        # Get all modules
        modules = get_all_submodules(griptape_tools)

        # Add the base package
        modules.append(griptape_tools)

        # Reload all modules in reverse (dependencies first)
        for module in reversed(modules):
            print(f"Reloading {module.__name__}")
            importlib.reload(module)

        rebuild_menu()
        print("Griptape tools reloaded successfully!")
    except Exception as e:
        cmds.warning(f"Failed to reload Griptape tools: {e}")
