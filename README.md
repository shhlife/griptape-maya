# Griptape Maya Tools

A collection of Maya tools and utilities built with Griptape.

## Installation

1. Clone this repository:
```bash
git clone https://github.com/shhlife/griptape-maya.git
```

2. Install dependencies using Poetry (in the `env` directory)

```bash
cd griptape-maya
poetry install --no-root
```

3. Make sure your Module file points to the right spot

The `griptape-maya.mod` file needs to point to your local repository path where _this project_ sits. 
Edit the path in griptape-maya.mod to match your system:

```bash
# macOS/Linux
+ griptape-maya 1.0 ~/Documents/GitHub/griptape-maya/src

# Windows
+ griptape-maya 1.0 %USERPROFILE%\Documents\GitHub\griptape-maya\src
```

4. Put the `griptape-maya.mod` file in the MAYA_MODULE_PATH

In order for Maya to find this module, it needs to know where to look for it. To do this, you need to put a copy of (or a symlink to) this file in one of the paths Maya expects.

Maya looks for this folder in the following environment variable: `MAYA_MODULE_PATH`. You can learn more about Maya environment variables here: https://help.autodesk.com/view/MAYAUL/2025/ENU/?guid=GUID-F480BE6D-47EE-49C9-A0DB-FB2675907CA2.

If you're still unsure, you can check where maya _thinks_ it should be by opening up Maya and in the _Python_ script editor execute:

```python
import os

os.getenv("MAYA_MODULE_PATH")
```

You'll see something like:

```
# Result: ('C:/Program '
#  'Files/Autodesk/Maya2025/modules;C:/Users/jason/OneDrive/Documents/maya/2025/modules;C:/Users/jason/OneDrive/Documents/maya/modules;C:/Program '
#  'Files/Common Files/Autodesk Shared/Modules/maya/2025')
```

As long as the `griptape-maya.mod` file is in one of those locations, this should work. The following code demonstrates how to create a symbolic link to the mod file in either mac, linux, or windows - you'll need to adjust the paths for your particular situation.

```bash
# macOS/Linux
mkdir -p ~/Library/Preferences/Autodesk/maya/modules
ln -s ~/Documents/GitHub/griptape-maya/griptape-maya.mod ~/Library/Preferences/Autodesk/maya/modules/griptape-maya.mod

# Windows cmd
# Note: On Windows you may need to run the command prompt as Administrator to create symbolic links.
# Make sure to run this in the `cmd` window, not PowerShell
mkdir "%USERPROFILE%\OneDrive\Documents\maya\modules"
mklink "%USERPROFILE%\OneDrive\Documents\maya\modules\griptape-maya.mod" "%USERPROFILE%\Documents\GitHub\griptape-maya\griptape-maya.mod"

# Windows PowerShell
# Note: On Windows you may need to run this as Administrator
# Create the modules directory
New-Item -ItemType Directory -Path "$env:USERPROFILE\OneDrive\Documents\maya\modules" -Force

# Create the symbolic link
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\OneDrive\Documents\maya\modules\griptape-maya.mod" -Target "$env:USERPROFILE\Documents\GitHub\griptape-maya\griptape-maya.mod"

```



5. Run Maya

Re-launch Maya. It should pick up the module file correctly, and if you check your script editor history and scroll up you should see something like:

```bash
---------------------------------------------
Initializing Griptape Tools...
SSL certificates configured for darwin
Added virtual environment to Python path: /Users/jason/Documents/GitHub/griptape-maya/.venv/lib/python3.11/site-packages
Griptape Tools initialized successfully
---------------------------------------------
```

## Directory Structure

```bash
griptape-maya/
├── src/
│   ├── scripts/         # Python scripts
│   ├── shelves/         # Maya shelf buttons
│   └── icons/           # Tool icons
├── tests/               # Unit tests
├── griptape-maya.mod    # Maya module file
├── pyproject.toml       # Poetry configuration
└── requirements.txt     # Requirements
```
