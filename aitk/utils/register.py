import importlib
import json
from pathlib import Path

from aitk.translators.base import BaseTranslator


def register_translator(
    translator_file: Path | str, translator_args: dict
) -> BaseTranslator:
    """get the translator object from the translator file

    Args:
        translator_file (Path | str): the path to the translator file
        translator_args (dict): the arguments for the translator

    Raises:
        AttributeError: The translator file does not have register method

    Returns:
        BaseTranslator: The translator object
    """
    if isinstance(translator_file, str):
        translator_file = Path(translator_file)

    translator_module = f"aitk.translators.{translator_file.stem}"
    module = importlib.import_module(translator_module)
    if hasattr(module, "register"):
        cls = module.register(translator_args)
        return cls
    else:
        raise AttributeError(
            f"translator {translator_file.stem} does not have a register method"
        )


def register_tasks(task_path: str) -> list[dict]:
    """register tasks

    Args:
        task_path (str, optional): a jsonl file that contains the tasks.

    Returns:
        list[dict]: a list of tasks
    """
    return register_tasks_jsonl(task_path)


def register_tasks_jsonl(file: str) -> list[dict]:
    with open(file, "r") as f:
        tasks = [json.loads(line) for line in f]

    app_info = {}
    for task in tasks:
        if task["app"] not in app_info:
            app_info[task["app"]] = task["app_package"]
        else:
            if app_info[task["app"]] != task["app_package"]:
                raise ValueError(
                    f"Task {task['name']} has different app package: {task['app_package']} != {app_info[task['app']]}"
                )

    return tasks, app_info


def register_tasks_py() -> list[dict]:
    """get the tasks

    Returns:
        list[dict]: a list contains dictionaries containing the `task` and `eval` function
    """

    ret_tasks = []
    task_dir = Path(__file__).parent.parent / "tasks"

    for task_file in task_dir.glob("*.py"):
        task_module = f"aitk.tasks.{task_file.stem}"
        module = importlib.import_module(task_module)
        if hasattr(module, "task"):
            task_dict = module.task()
        else:
            raise AttributeError(f"task {task_file.stem} does not have a task")

        ret_tasks.append(
            {
                "name": task_file.stem,
                **task_dict,
                "eval": module.eval if hasattr(module, "eval") else None,
            }
        )

    return ret_tasks
