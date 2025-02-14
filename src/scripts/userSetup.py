# src/scripts/userSetup.py
import os
import sys

import maya.cmds as cmds
import maya.utils


def get_venv_site_packages():
    """Get the path to the virtual environment's site-packages"""
    # Get the module path first
    module_path = cmds.moduleInfo(moduleName="griptape-maya", path=True)

    # Get current Python version
    py_version = f"python{sys.version_info.major}.{sys.version_info.minor}"

    # Go up from src to project root and into .venv with correct Python version
    venv_path = os.path.join(
        os.path.dirname(module_path), ".venv", "lib", py_version, "site-packages"
    )

    if os.path.exists(venv_path):
        return venv_path
    else:
        cmds.warning(f"Virtual environment not found at: {venv_path}")
        return None


def setup_ssl():
    """Setup SSL certificates based on OS"""
    if sys.platform == "darwin":  # macOS
        cert_path = "/etc/ssl/cert.pem"
    elif sys.platform == "win32":  # Windows
        # Windows usually handles certificates through the OS
        # but we can point to Python's default location if needed
        cert_path = os.path.join(
            os.path.dirname(sys.executable),
            "Lib",
            "site-packages",
            "certifi",
            "cacert.pem",
        )
    else:  # Linux
        cert_path = "/etc/ssl/certs/ca-certificates.crt"  # Common Linux location

    if os.path.exists(cert_path):
        os.environ["SSL_CERT_FILE"] = cert_path
        print(f"SSL certificates configured for {sys.platform}")
    else:
        cmds.warning(f"Could not find SSL certificates at {cert_path}")


def initialize_griptape():
    try:
        import griptape_tools.core as core

        print("---------------------------------------------")
        print("Initializing Griptape Tools...")

        setup_ssl()

        # Add venv to path
        venv_path = get_venv_site_packages()
        if venv_path:
            sys.path.append(venv_path)
            print(f"Added virtual environment to Python path: {venv_path}")

        core.rebuild_menu()
        print("Griptape Tools initialized successfully")
        print("---------------------------------------------")
    except Exception as e:
        cmds.warning(f"Failed to initialize Griptape Tools: {e}")


# sys.path.append(
#     "/Users/jason/Documents/GitHub/griptape-maya/.venv/lib/python3.11/site-packages"
# )
maya.utils.executeDeferred(initialize_griptape)
