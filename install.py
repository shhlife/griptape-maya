import json
import os
import subprocess
import sys
import time
from pathlib import Path


# Color formatting
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def header(text):
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")


def info(text):
    print(f"{Colors.BLUE}{text}{Colors.ENDC}")


def success(text):
    print(f"{Colors.GREEN}{text}{Colors.ENDC}")


def warning(text):
    print(f"{Colors.YELLOW}{text}{Colors.ENDC}")


def error(text):
    print(f"{Colors.RED}{text}{Colors.ENDC}")


def highlight(text):
    print(f"{Colors.CYAN}{text}{Colors.ENDC}")


def find_existing_module():
    """Find existing griptape-maya.mod files"""
    existing_installations = []

    # Check all possible module paths
    for path in get_maya_module_paths():
        mod_file = path / "griptape-maya.mod"
        if mod_file.exists():
            existing_installations.append(mod_file)

    return existing_installations


def get_mayapy_path():
    """Get the path to mayapy based on the operating system"""
    if sys.platform == "win32":
        maya_paths = [
            r"C:\Program Files\Autodesk\Maya2025\bin\mayapy.exe",
            r"C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe",
            r"C:\Program Files\Autodesk\Maya2023\bin\mayapy.exe",
        ]
    elif sys.platform == "darwin":
        maya_paths = [
            "/Applications/Autodesk/maya2025/Maya.app/Contents/bin/mayapy",
            "/Applications/Autodesk/maya2024/Maya.app/Contents/bin/mayapy",
            "/Applications/Autodesk/maya2023/Maya.app/Contents/bin/mayapy",
        ]
    else:  # Linux
        maya_paths = [
            "/usr/autodesk/maya2025/bin/mayapy",
            "/usr/autodesk/maya2024/bin/mayapy",
            "/usr/autodesk/maya2023/bin/mayapy",
        ]

    for path in maya_paths:
        if Path(path).exists():
            return path

    return None


def get_default_maya_module_paths():
    """Get default Maya module paths based on OS"""
    paths = []
    if sys.platform == "win32":
        # Maya installation paths
        paths.extend(
            [
                Path(r"C:/Program Files/Autodesk/Maya2025/modules"),
                Path(
                    r"C:/Program Files/Common Files/Autodesk Shared/Modules/maya/2025"
                ),
            ]
        )

        # User paths
        user_paths = [
            Path(
                os.path.expandvars(
                    r"%USERPROFILE%/OneDrive/Documents/maya/2025/modules"
                )
            ),
            Path(os.path.expandvars(r"%USERPROFILE%/OneDrive/Documents/maya/modules")),
            Path(os.path.expandvars(r"%USERPROFILE%/Documents/maya/2025/modules")),
            Path(os.path.expandvars(r"%USERPROFILE%/Documents/maya/modules")),
        ]
        paths.extend(user_paths)
    elif sys.platform == "darwin":
        paths.extend(
            [
                Path("/Applications/Autodesk/maya2025/Maya.app/Contents/modules"),
                Path("~/Library/Preferences/Autodesk/maya/2025/modules").expanduser(),
                Path("~/Library/Preferences/Autodesk/maya/modules").expanduser(),
            ]
        )
    else:  # Linux
        paths.extend(
            [
                Path("/usr/autodesk/maya2025/modules"),
                Path("~/maya/2025/modules").expanduser(),
                Path("~/maya/modules").expanduser(),
            ]
        )
    return paths


def get_maya_module_paths():
    """Get all Maya module paths using multiple methods"""
    paths = set()  # Use a set to avoid duplicates

    # Method 1: Try using mayapy
    mayapy = get_mayapy_path()
    if mayapy:
        try:
            cmd = [
                mayapy,
                "-c",
                "import os; print('MAYA_MODULE_PATH=' + os.getenv('MAYA_MODULE_PATH', ''))",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            env_paths = (
                result.stdout.strip().replace("MAYA_MODULE_PATH=", "").split(os.pathsep)
            )
            paths.update(Path(p) for p in env_paths if p)
        except subprocess.CalledProcessError:
            warning("Could not get module paths from mayapy")

    # Method 2: Check environment variable directly
    maya_module_path = os.getenv("MAYA_MODULE_PATH")
    if maya_module_path:
        paths.update(Path(p) for p in maya_module_path.split(os.pathsep) if p)

    # Method 3: Add default paths
    paths.update(get_default_maya_module_paths())

    # Filter out empty strings and normalize paths
    valid_paths = []
    seen_paths = set()
    for path in paths:
        try:
            normalized_path = str(path.resolve() if path.exists() else path)
            if normalized_path not in seen_paths:
                seen_paths.add(normalized_path)
                valid_paths.append(path)
        except Exception:
            continue

    return valid_paths


def get_user_module_choice(module_paths):
    """Let user choose where to install the module"""
    info("\nAvailable Maya module paths:")
    valid_paths = []

    for i, path in enumerate(module_paths, 1):
        exists = path.exists()
        valid_paths.append(path)
        highlight(f"{i}. {path} {'(exists)' if exists else '(does not exist)'}")

    # Add option to specify custom path
    highlight(f"{len(valid_paths) + 1}. Specify a custom path")

    while True:
        try:
            choice = input(
                "\nWhere would you like to install the module? (enter number): "
            )
            choice = int(choice)
            if 1 <= choice <= len(valid_paths):
                chosen_path = valid_paths[choice - 1]
                if not chosen_path.exists():
                    create = input(
                        f"\nDirectory {chosen_path} does not exist. Create it? (y/n): "
                    )
                    if create.lower() != "y":
                        continue
                    chosen_path.mkdir(parents=True, exist_ok=True)
                return chosen_path
            elif choice == len(valid_paths) + 1:
                custom_path = input("Enter custom path: ")
                custom_path = Path(custom_path).expanduser().resolve()
                if not custom_path.exists():
                    create = input(
                        f"\nDirectory {custom_path} does not exist. Create it? (y/n): "
                    )
                    if create.lower() != "y":
                        continue
                    custom_path.mkdir(parents=True, exist_ok=True)
                return custom_path
        except ValueError:
            pass
        error("Please enter a valid number.")


def confirm_step(message):
    """Get user confirmation for a step"""
    while True:
        response = input(f"\n{message} (y/n): ")
        if response.lower() in ["y", "n"]:
            return response.lower() == "y"


def install_module(module_dir):
    """Install the module for the current platform"""
    # Get the project root directory
    project_root = Path(__file__).parent.absolute()

    # Create the .mod file path
    mod_file = module_dir / "griptape-maya.mod"

    # Write the .mod file content with absolute paths
    mod_content = f"+ griptape-maya 1.0 {project_root}/src\n"
    mod_content += "scripts: scripts\n"
    mod_content += "icons: icons\n"
    mod_content += "shelves: shelves\n"

    # Write the .mod file
    mod_file.write_text(mod_content)
    success(f"Created .mod file at: {mod_file}")
    info(f"Module configured to use source from: {project_root}/src")


def show_requirements():
    """Display the requirements that will be installed"""
    req_file = Path("requirements.txt")

    # Generate requirements.txt if it doesn't exist
    if not req_file.exists():
        try:
            info("Generating requirements.txt from poetry...")
            subprocess.run(
                [
                    "poetry",
                    "export",
                    "-f",
                    "requirements.txt",
                    "--output",
                    "requirements.txt",
                ],
                check=True,
            )
            success("Generated requirements.txt from poetry")
        except subprocess.CalledProcessError:
            warning("Could not generate requirements.txt from poetry")
            return False
        except FileNotFoundError:
            warning("Poetry not found")
            return False

    if not req_file.exists():
        error("requirements.txt not found")
        return False

    # Read and display requirements
    requirements = req_file.read_text().strip().split("\n")
    info("\nThe following packages will be installed/upgraded:")
    header("----------------------------------------")
    for req in requirements:
        highlight(f"  {req}")
    header("----------------------------------------")
    return True


def install_requirements():
    """Install Python requirements using mayapy, attempting upgrade first"""
    mayapy = get_mayapy_path()
    if not mayapy:
        error("Could not find mayapy. Please ensure Maya is installed.")
        return False

    info(f"Using mayapy from: {mayapy}")

    # Show requirements and get confirmation
    if not show_requirements():
        return False

    if not confirm_step(
        "Would you like to proceed with installing/upgrading these packages?"
    ):
        warning("Package installation cancelled.")
        return False

    info("\nInstalling/upgrading Python requirements...")
    try:
        # Always upgrade pip first
        info("Upgrading pip...")
        subprocess.run([mayapy, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        success("Successfully upgraded pip")

        # Try to upgrade packages first
        try:
            info("\nAttempting to upgrade all packages to latest versions...")
            subprocess.run(
                [mayapy, "-m", "pip", "install", "--upgrade", "-r", "requirements.txt"],
                check=True,
            )
            success("Successfully upgraded all packages")
        except subprocess.CalledProcessError as e:
            warning("\nUpgrade failed, attempting regular install...")
            error(f"Upgrade error: {e}")
            subprocess.run(
                [mayapy, "-m", "pip", "install", "-r", "requirements.txt"], check=True
            )
            success("Successfully installed packages")
        return True
    except subprocess.CalledProcessError as e:
        error(f"Error installing requirements: {e}")
        return False


def main():
    header("\n=== Griptape Maya Tools Installation ===\n")

    # Step 1: Find Maya installation
    header("Step 1: Locating Maya installation...")
    mayapy = get_mayapy_path()
    if not mayapy:
        error("Error: Could not find Maya installation. Installation cancelled.")
        return
    success(f"Found Maya Python at: {mayapy}")
    time.sleep(1)

    # Check for existing installations
    existing_mods = find_existing_module()
    if existing_mods:
        info("\nFound existing griptape-maya installation(s):")
        for mod_file in existing_mods:
            highlight(f"  {mod_file}")
            if mod_file.exists():
                info("Current configuration:")
                print(mod_file.read_text())

        action = input(
            "\nWhat would you like to do?\n"
            "1. Reinstall module (will overwrite existing installation)\n"
            "2. Skip module installation (keep existing)\n"
            "3. Install in a new location\n"
            "Choice (1-3): "
        )

        if action == "2":
            info("\nSkipping module installation.")
        elif action == "3":
            info("\nProceeding with new installation...")
        else:  # Default to reinstall
            info("\nProceeding with reinstallation...")

    # Only proceed with module installation if not skipping
    if not existing_mods or action != "2":
        # Step 2: Choose module installation location
        header("\nStep 2: Choosing module installation location...")
        module_paths = get_maya_module_paths()
        if not module_paths:
            warning(
                "Warning: No Maya module paths found. You may need to set MAYA_MODULE_PATH."
            )
            if not confirm_step("Continue anyway?"):
                return

        chosen_path = get_user_module_choice(module_paths)
        success(f"\nChosen installation path: {chosen_path}")

        if not confirm_step("Proceed with module installation?"):
            warning("Installation cancelled.")
            return

        # Step 3: Install module
        header("\nStep 3: Installing module...")
        try:
            install_module(chosen_path)
            success("Module installation successful!")
        except Exception as e:
            error(f"Error installing module: {e}")
            return

    # Step 4: Install/Upgrade Python packages
    header("\nStep 4: Installing/Upgrading Python packages...")
    if install_requirements():
        success("\nPython requirements processed successfully!")
    else:
        warning("\nWarning: There were some issues with Python requirements.")
        if not confirm_step("Continue anyway?"):
            return
    # Add IDE setup information
    header("\n=== IDE Setup ===")
    info("For code completion in your IDE, set your Python interpreter to:")
    if sys.platform == "win32":
        interpreter_path = Path(mayapy).parent / "python.exe"
    else:
        interpreter_path = mayapy
    highlight(f"  {interpreter_path}")

    info("\nVS Code setup:")
    info("1. Create or edit .vscode/settings.json in your project")
    info("2. Add these settings:")
    highlight(
        json.dumps(
            {"python.defaultInterpreterPath": str(interpreter_path).replace("\\", "/")},
            indent=2,
        )
    )

    info("\nPyCharm setup:")
    info("1. Open Project Settings > Project Interpreter")
    info(f"2. Add the interpreter at: {interpreter_path}")

    # Final confirmation and instructions
    header("\n=== Installation Complete ===")
    if not existing_mods or action != "2":
        success(f"\nModule installed to: {chosen_path}")
    else:
        success(f"\nUsing existing module at: {existing_mods[0]}")
    success(f"Python environment: {mayapy}")

    header("\nTo verify installation:")
    info("1. Restart Maya")
    info("2. Check script editor for initialization messages")
    info("3. You should see 'Griptape Tools initialized successfully'")


if __name__ == "__main__":
    main()
