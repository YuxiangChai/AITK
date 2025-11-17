__version__ = "0.2.1"


import platform
from pathlib import Path


def check_create_dir(path: Path) -> Path:
    if not path.is_dir():
        path.mkdir(parents=True)
    return path


def get_os() -> str:
    name = platform.system()
    if name == "Darwin":
        return "mac"
    elif name == "Linux":
        return "linux"
    elif name == "Windows":
        return "win"
    else:
        raise ValueError(f"Unsupported OS: {name}")
