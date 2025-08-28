import argparse
import base64
import io
import subprocess
import time
from pathlib import Path

import yaml
from PIL import Image

from aitk import aitk_logger, check_create_dir
from aitk.utils.adb_controller import ADBController
from aitk.utils.appium_controller import AppiumController
from aitk.utils.avd_manager import AVDManager
from aitk.utils.register import register_tasks, register_translator


def is_stuck(img: base64) -> bool:
    image_data = base64.b64decode(img)
    image_pil = Image.open(io.BytesIO(image_data))
    center_image = image_pil.crop((0, 100, controller.w, controller.h - 100))
    for pixel in center_image.getdata():
        if pixel != (0, 0, 0):
            return False
    return True


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", type=str, default="configs/controller.yaml")
    parser.add_argument("--experiment-name", "-e", type=str)
    parser.add_argument("--resume-exp", "-r", type=str)
    parser.add_argument("--avd-name", "-a", type=str)
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = get_args()

    with open(args.config, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    translator = register_translator(config["translator"], config["translator_args"])
    tasks, app_info = register_tasks(config["experiment"]["tasks"])

    if args.experiment_name:
        config["experiment"]["name"] = args.experiment_name

    if args.resume_exp:
        config["experiment"]["resume_exp"] = args.resume_exp

    if args.avd_name:
        config["device"]["avd_name"] = args.avd_name

    existing_tasks = []
    if config["experiment"]["resume_exp"]:
        resume_dir = Path(config["experiment"]["resume_exp"])
        aitk_logger.info(f"Resume from {resume_dir}...")
        for task_dir in resume_dir.iterdir():
            if (task_dir / "history.json").exists():
                existing_tasks.append(task_dir.name)
        save_root_dir = resume_dir
    else:
        save_root_dir = Path(config["experiment"]["save_root_dir"])
        save_root_dir = save_root_dir / config["experiment"]["name"]
        if save_root_dir.exists():
            aitk_logger.info(f"{save_root_dir} exists. Resuming...")
            for task_dir in save_root_dir.iterdir():
                if (task_dir / "history.json").exists():
                    existing_tasks.append(task_dir.name)
        else:
            aitk_logger.info(f"Running experiment at: {save_root_dir}")
            check_create_dir(save_root_dir)

    avd_manager = AVDManager()
    running_avd_list = avd_manager.get_running_avd_list()
    if running_avd_list == []:
        aitk_logger.info("No running AVD found. Starting a new AVD duplicate...")
        avd_manager.duplicate_avd(config["device"]["avd_name"])
        cmd = ["emulator", "-avd", config["device"]["avd_name"], "-no-snapshot"]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(60)
    else:
        aitk_logger.info(f"Running AVD found.")

    device_udid = config["device"]["udid"]
    if config["experiment"]["backend"] == "adb":
        controller = ADBController(config, app_info)
    elif config["experiment"]["backend"] == "appium":
        if "appium_port" in config["device"]:
            appium_port = config["device"]["appium_port"]
        else:
            appium_port = 4723
        controller = AppiumController(config, device_udid, app_info, appium_port)

    task_idx = 0
    while task_idx < len(tasks):
        # check if the AVD is running
        running_avd_list = avd_manager.get_running_avd_list()
        if running_avd_list is None:
            aitk_logger.error("No running AVD found. Starting a new AVD duplicate...")
            avd_manager.duplicate_avd(config["device"]["avd_name"])
            cmd = ["emulator", "-avd", config["device"]["avd_name"], "-no-snapshot"]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(60)

            if config["experiment"]["backend"] == "appium":
                if "appium_port" in config["device"]:
                    appium_port = config["device"]["appium_port"]
                else:
                    appium_port = 4723
                controller = AppiumController(
                    config, device_udid, app_info, appium_port
                )

            # check if the last task is finished
            if task_idx > 0:
                task_idx -= 1
                last_task = tasks[task_idx]
                last_task_name = last_task["name"]
                folder = save_root_dir / last_task_name
                if folder.exists() and (folder / "history.json").exists():
                    aitk_logger.info(
                        f"Last task {last_task_name} already exists, skipping..."
                    )
                    task_idx += 1
                    continue
                else:
                    aitk_logger.info(
                        f"Last task {last_task_name} is not finished, resuming..."
                    )

        task = tasks[task_idx]
        crash_flag = False
        try:
            task_name = task["name"]
            if task_name in existing_tasks:
                aitk_logger.info(f"Task {task_name} already exists, skipping...")
                task_idx += 1
                continue

            task_str = task["task"]  # task description
            save_dir = save_root_dir / task["name"]  # task file name
            check_create_dir(save_dir)

            max_steps = (
                task["max_steps"] if "max_steps" in task else 30
            )  # default max steps is 50 so that a task won't run forever

            state_save_dir = check_create_dir(save_dir / "states")

            controller.set_task_eval(**task)
            controller.save_state(state_save_dir)  # save the initial state

            if config["experiment"]["screen_record"]:
                assert (
                    config["experiment"]["backend"] == "appium"
                ), "Screen recording only support Appium as backend. ADB doesn't support yet."
                controller.start_record(config["experiment"]["record_resolution"])

            while True:
                if controller.step >= max_steps:
                    aitk_logger.info(
                        f"Task {task['name']} reached max steps: {max_steps}. Ending task..."
                    )
                    break

                if controller.step == 0:
                    aitk_logger.info(
                        f"Task started: {task['name']} ----- {task['task']}\n---------------------------------------"
                    )
                aitk_logger.info(f"Step {controller.step}: ")

                state = controller.get_state()
                # if the emulator is stuck (all screen is black), kill the avd and start over
                screenshot = state["screenshot"]
                if is_stuck(screenshot):
                    avd_running_devices = avd_manager.get_running_avd_list()
                    avd = avd_running_devices[0]["udid"]
                    kill_cmd = ["adb", "-s", avd, "emu", "kill"]
                    subprocess.Popen(
                        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    avd_manager.delete_avd()
                    crash_flag = True
                    break

                history = controller.get_history()

                # agent communication
                agent_response = translator.to_agent(task_str, state, history)
                # aitk_logger.info(f"Agent response: {agent_response}")
                controller.save_history_agent_message(agent_response)

                # translate the agent response to action space in AITK
                action_dict = translator.to_device(
                    agent_response, controller.w, controller.h
                )
                aitk_logger.info(f"Action dict: {action_dict}")

                # execute the action
                try:
                    controller.exe_action(action_dict)
                except Exception as e:
                    aitk_logger.error(f"Task execution failed: {e}")
                    controller.exe_action(
                        {"action": "end", "answer": f"task execution failed: {e}"}
                    )

                if action_dict["action"] == "end":
                    break

                time.sleep(1)

                if controller.step < max_steps:
                    controller.save_state(state_save_dir)

            if crash_flag:
                continue

            if config["experiment"]["screen_record"]:
                controller.stop_save_record(save_dir)

            try:
                controller.save_history(save_dir)
                aitk_logger.info(f"Task saved: {task['name']}")
            except Exception as e:
                aitk_logger.error(f"Task save failed: {e}")

            aitk_logger.info(f"Task finished: {task['name']}")
            task_idx += 1
        except Exception as e:
            aitk_logger.error(f"Error in task {task['name']}: {e}")
            task_idx += 1

    aitk_logger.info(f"Turn off the emulator...")

    subprocess.Popen(
        ["adb", "-e", "emu", "kill"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
