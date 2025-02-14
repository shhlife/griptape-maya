# Griptape Maya Tools

A collection of Maya tools and utilities built with Griptape.

## Installation

1. Clone this repository:
```bash
git clone https://github.com/shhlife/griptape-maya.git
```

2. Run `install.py`

In order for this module to work, you'll need to create a `griptape-maya.mod` file in the location where Maya can find it, and install the appropriate griptape libraries in Maya's python.

We've automated this process as much as possible for you. Use the `install.py` script to do it.

```bash
cd griptape-maya
python install.py
```

Follow the instructions. :)

## Updating

To get the latest version, you should be able to just do:

```bash
cd griptape-maya
git pull
```

and that'll grab the latest code. If you want to just double-check and make sure all your libraries are up to date you can do:

```bash
python install.py
```

and it'll run through the install again, updating only what's required.