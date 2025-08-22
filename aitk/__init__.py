__version__ = "0.2.1"


import logging
import platform
from pathlib import Path

aitk_logger = logging.getLogger("AITK - Controller")
aitk_logger.setLevel(logging.INFO)  # Or DEBUG, WARNING, etc.

# Prevent adding multiple handlers if re-imported
if not aitk_logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )
    handler.setFormatter(formatter)
    aitk_logger.addHandler(handler)


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
