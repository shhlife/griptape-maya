import os
import sys
from pathlib import Path

import maya.cmds as cmds
import maya.utils
from griptape_tools.api_keys import API_KEYS  # ✅ Import API key definitions
from griptape_tools.menu import create_menu


def load_api_keys():
    """Load API keys from Maya optionVars and set them as environment variables."""
    for key in API_KEYS.keys():
        if cmds.optionVar(exists=key):
            os.environ[key] = cmds.optionVar(q=key)  # Set environment variable

    print("[Maya] API keys loaded into environment variables.")


def get_ssl_cert_path():
    """Get SSL certificate path based on platform"""
    if sys.platform == "darwin":  # macOS
        cert_paths = [
            Path("/etc/ssl/cert.pem"),
            Path("/usr/local/etc/openssl/cert.pem"),
        ]
    elif sys.platform == "win32":  # Windows
        cert_paths = [
            Path(sys.executable).parent
            / "lib"
            / "site-packages"
            / "certifi"
            / "cacert.pem",
        ]
    else:  # Linux
        cert_paths = [
            Path("/etc/ssl/certs/ca-certificates.crt"),
            Path("/etc/pki/tls/certs/ca-bundle.crt"),
        ]

    # Return the first existing cert path
    for cert_path in cert_paths:
        if cert_path.exists():
            return str(cert_path)

    return None


def setup_ssl():
    """Setup SSL certificates"""
    cert_path = get_ssl_cert_path()
    if cert_path:
        os.environ["SSL_CERT_FILE"] = cert_path
        print(f"SSL certificates configured: {cert_path}")
    else:
        cmds.warning("Could not find SSL certificates")


def initialize_griptape():
    try:
        print("---------------------------------------------")
        print("Starting Griptape Tools initialization...")

        print("\nInitial Python Environment:")
        print(f"Python executable: {sys.executable}")
        print(f"Python version: {sys.version}")

        print("\nAttempting to import griptape_tools.core...")

        print("Successfully imported griptape_tools.core")

        print("\nSetting up SSL...")
        setup_ssl()

        print("\nCreating menu...")
        try:
            create_menu()
            print("Griptape menu initialized")
        except Exception as e:
            cmds.warning(f"Failed to create Griptape menu: {str(e)}")

        print("Griptape Tools initialized successfully")
        print("---------------------------------------------")
    except Exception as e:
        cmds.warning(f"Failed to initialize Griptape Tools: {str(e)}")
        import traceback

        print("\nFull traceback:")
        traceback.print_exc()
        cmds.warning("Check script editor for full error details")


# Run these on maya startup
load_api_keys()
maya.utils.executeDeferred(initialize_griptape)
