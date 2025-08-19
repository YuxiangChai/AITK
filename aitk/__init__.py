__version__ = "0.1.0"


import logging
import platform
import subprocess
from pathlib import Path

from openai import OpenAI

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


def answer_correct_judge(
    question: str,
    answer: str,
    gt: str,
    client: OpenAI,
    model: str = "gpt-4.1-mini",
) -> bool:

    prompt = f"You need to judge whether the answer is correct or not based on the ground truth answer. The question is '{question}'. The ground truth answer is '{gt}'. You need to judge whether the answer '{answer}' is correct (similar or include the same information as ground truth) or not. If the answer is correct, please only output 'Yes'. If the answer is incorrect, please only output 'No'."

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=10,
    )

    judge = response.choices[0].message.content
    judge = judge.strip()
    if judge == "Yes":
        return True
    else:
        return False


def install_app(apk_paths: list[Path | str], udid: str) -> None:
    if len(apk_paths) == 1:
        cmd = f"adb -s {udid} install {apk_paths[0].as_posix()}"
    else:
        cmd = f"adb -s {udid} install-multiple {' '.join([apk.as_posix() for apk in apk_paths])}"
    e = subprocess.check_output(cmd, shell=True)
    out = e.decode("utf-8")
    print(out.replace("\n", " "))


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
