import base64
import json
import logging
import subprocess
import time
from pathlib import Path

import dill

from aitk import aitk_logger, check_create_dir
from aitk.utils.keycode import KEYCODE


class ADBController:
    def __init__(
        self,
        config: dict,
        app_info: dict = None,
    ) -> None:
        self.app_info = app_info

        wh = self.driver.get_window_size()
        self.w = wh["width"]
        self.h = wh["height"]

        self.history = {
            "xmls": [],
            "screenshots": [],
            "actions": [],
            "agent_messages": [],
            "packages": [],
            "activities": [],
        }
        self.config = config
        self.logger = aitk_logger
        self.step = 0

    def _get_xml(self) -> str:
        """
        get the xml of the current state of the device

        Returns:
            str: the xml of the current state of the device
        """
        cmd = ["adb", "exec-out", "uiautomator dump /dev/stdout"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            self.logger.log(logging.ERROR, f"Failed to get XML: {e}")
            return "No XML"

    def _get_screenshot(self) -> str:
        """get current screenshot of the device, return a base64 string

        Returns:
            str: a base64 string of the screenshot
        """
        cmd = ["adb", "exec-out", "screencap -p"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            png_data = base64.b64encode(result.stdout.encode("utf-8")).decode("utf-8")
            return png_data
        except subprocess.CalledProcessError as e:
            self.logger.log(logging.ERROR, f"Failed to get screenshot: {e}")
            return "No screenshot"

    def _open(self, app: str) -> None:
        for key, value in self.app_info.items():
            if key.lower() in app.lower():
                app_package = value
                break
        if app_package:
            cmd = [
                "adb",
                "shell",
                "monkey",
                "-p",
                app_package,
                "-c",
                "android.intent.category.LAUNCHER",
                "1",
            ]
            subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            self.logger.log(logging.INFO, f"App {app} not found.")

    def _tap(self, x: int, y: int) -> None:
        cmd = ["adb", "shell", "input", "tap", str(x), str(y)]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _long_press(self, x: int, y: int, duration: int = 1000) -> None:
        cmd = [
            "adb",
            "shell",
            "input",
            "swipe",
            str(x),
            str(y),
            str(x),
            str(y),
            str(duration),
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 1000) -> None:
        cmd = [
            "adb",
            "shell",
            "input",
            "swipe",
            str(x1),
            str(y1),
            str(x2),
            str(y2),
            str(duration),
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _clear(self) -> None:
        cmd = [
            "adb",
            "shell",
            "input",
            "keyevent",
            str(KEYCODE["DEL"]),
        ]
        for _ in range(20):
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.2)

    def _type(self, text: str) -> None:
        cmd = [
            "adb",
            "shell",
            "input",
            "text",
            text,
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _enter(self) -> None:
        cmd = [
            "adb",
            "shell",
            "input",
            "keyevent",
            str(KEYCODE["ENTER"]),
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)

    def _back(self) -> None:
        cmd = [
            "adb",
            "shell",
            "input",
            "keyevent",
            str(KEYCODE["BACK"]),
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)

    def _home(self) -> None:
        cmd = [
            "adb",
            "shell",
            "input",
            "keyevent",
            str(KEYCODE["HOME"]),
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)

    def _all_apps(self) -> None:
        cmd = [
            "adb",
            "shell",
            "input",
            "keyevent",
            str(KEYCODE["ALL_APPS"]),
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)

    def _wait(self, duration: int = 3) -> None:
        time.sleep(duration)

    def _terminate_all_apps(self) -> None:
        # self._home()
        self._all_apps()
        self._swipe(
            int(0.1 * self.w),
            int(0.5 * self.h),
            int(0.9 * self.w),
            int(0.5 * self.h),
            100,
        )
        time.sleep(1)
        self._tap(int(0.2 * self.w), int(0.48 * self.h))
        time.sleep(1.5)

    def start_record(self, resolution: list[int]) -> None:
        """start recording the screen

        Args:
            resolution (list[int]): the resolution of the screen
        """
        self.driver.start_recording_screen(videoSize=f"{resolution[0]}x{resolution[1]}")

    def stop_save_record(self, save_path: Path) -> None:
        """stop recording the screen and save the video

        Args:
            save_path (Path): the path to save the video
        """
        recording = self.driver.stop_recording_screen()
        recording = base64.b64decode(recording)
        with open(save_path / f"process.mp4", "wb") as f:
            f.write(recording)

    def get_state(self) -> dict:
        """get current state of the device

        Returns:
            dict: a dictionary containing the current state of the device
            - xml: the XML of the current state of the device in string format
            - screenshot: the screenshot of the current state of the device in base64 format
            - package: the package of the current app
        """
        xml = self._get_xml()
        screenshot = self._get_screenshot()
        package = self.driver.current_package
        activity = self.driver.current_activity

        return {
            "xml": xml,
            "screenshot": screenshot,
            "package": package,
            "activity": activity,
        }

    def save_state(self, save_path: Path) -> None:
        """save the current state of the device

        Args:
            save_path (Path): the path to save the state
        """
        screenshot_dir = check_create_dir(save_path / "screenshots")
        xml_dir = check_create_dir(save_path / "xmls")
        state = self.get_state()
        with open(screenshot_dir / f"step_{self.step}.png", "wb") as f:
            screenshot = base64.b64decode(state["screenshot"])
            f.write(screenshot)

        with open(xml_dir / f"step_{self.step}.xml", "w") as f:
            f.write(state["xml"])

        self.history["screenshots"].append(state["screenshot"])
        self.history["xmls"].append(state["xml"])
        self.history["packages"].append(state["package"])
        self.history["activities"].append(state["activity"])

    def get_history(self) -> dict:
        """get the history of the device in the current task

        Returns:
            dict: the history of the device
        """
        return self.history

    def save_history(self, save_path: Path) -> None:
        """save the history of the device in the current task

        Args:
            save_path (Path): the path to save the history
        """
        history = self.get_history()
        history_ = {
            "task": self.task,
            **self.kwargs,
            "steps": [],
        }

        for i in range(len(history["xmls"])):
            history_["steps"].append(
                {
                    "xml": f"step_{i}.xml",
                    "screenshot": f"step_{i}.png",
                    "action": history["actions"][i],
                    "agent_message": history["agent_messages"][i],
                    "package": history["packages"][i],
                    "activity": history["activities"][i],
                }
            )

        with open(save_path / f"history.json", "w") as f:
            json.dump(history_, f, indent=2)

        if self.eval is not None:
            with open(save_path / "eval_func.pkl", "wb") as f:
                dill.dump(self.eval, f)

    def save_history_agent_message(self, agent_message: str) -> None:
        """save the agent message of the current step

        Args:
            agent_message (str): the agent message
        """
        self.history["agent_messages"].append(agent_message)

    def exe_action(self, action: dict, save_flag: bool = True) -> None:
        """execute action on the device

        Args:
            action (dict): action to be executed
            save_flag (bool, optional): whether to save the action. Defaults to True.
        """
        if action["action"] == "open":
            self._open(action["app"])
        elif action["action"] == "tap":
            self._tap(action["x"], action["y"])
        elif action["action"] == "long_press":
            self._long_press(action["x"], action["y"])
        elif action["action"] == "swipe":
            if "duration" in action:
                self._swipe(
                    action["x1"],
                    action["y1"],
                    action["x2"],
                    action["y2"],
                    action["duration"],
                )
            else:
                self._swipe(action["x1"], action["y1"], action["x2"], action["y2"])
        elif action["action"] == "type":
            # clear the input field
            if (
                "clear_before_type" in self.config
                and not self.config["clear_before_type"]
            ):
                pass
            else:
                self._clear()
            self._type(action["text"])
        elif action["action"] == "enter":
            self._enter()
        elif action["action"] == "back":
            self._back()
        elif action["action"] == "home":
            self._home()
        elif action["action"] == "wait":
            self._wait(action["duration"])
        elif action["action"] == "end":
            if self.logger is not None and save_flag:
                self.logger.log(logging.INFO, f"Task Finished.")

        if save_flag:
            self.history["actions"].append(action)
        self.step += 1

    def set_task_eval(self, **kwargs) -> None:
        """set the task and evaluation function and also start a new history.

        Args:
            **kwargs: arguments for the task, which contains a task string, an optional evaluation function and additional arguments for the task, such as task level, task category, etc.
        """
        self.step = 0
        self.kwargs = kwargs
        self.task = self.kwargs.pop("task", None)
        self.eval = self.kwargs.pop("eval", None)
        self.history = {
            "xmls": [],
            "screenshots": [],
            "actions": [],
            "agent_messages": [],
            "packages": [],
            "activities": [],
        }

        self._terminate_all_apps()
