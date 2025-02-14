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
poetry install
```

3. Make sure your Module file points to the right spot

The `griptape-maya.mod` file needs to point to your local repository path. Edit the path in griptape-maya.mod to match your system:

```bash
# macOS/Linux
+ griptape-maya 1.0 ~/Documents/GitHub/griptape-maya/src

# Windows
+ griptape-maya 1.0 %USERPROFILE%\Documents\GitHub\griptape-maya\src
```

4. Create a symbolic link to the module file:

```bash
# macOS/Linux
mkdir -p ~/Library/Preferences/Autodesk/maya/modules
ln -s ~/Documents/GitHub/griptape-maya/griptape-maya.mod ~/Library/Preferences/Autodesk/maya/modules/griptape-maya.mod

# Windows cmd
# Note: On Windows you may need to run the command prompt as Administrator to create symbolic links
mkdir "%USERPROFILE%\Documents\maya\modules"
mklink "%USERPROFILE%\Documents\maya\modules\griptape-maya.mod" "PATH\TO\griptape-maya\griptape-maya.mod"
```



5. Run Maya

If you launch maya, it should pick up the module file correctly, and if you check your script editor history and scroll up you should see something like:

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
