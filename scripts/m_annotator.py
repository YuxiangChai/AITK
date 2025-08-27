import argparse
import ast
import base64
import copy
import json
import logging
import re
import shutil
import subprocess
import threading
import time
import tkinter as tk
import uuid
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageTk

from aitk import get_os


def get_output_path(path: Path, name: str, time_front: bool = False) -> Path:
    time = datetime.now()
    if time_front:
        name = f"{time.year}_{time.month}_{time.day}_{time.hour}_{time.minute}_{name}"
    else:
        name = f"{name}_{time.year}_{time.month}_{time.day}_{time.hour}_{time.minute}"
    return path / name


def check_create_dir(path: Path, silent: bool = False) -> Path:
    if not path.is_dir():
        path.mkdir(parents=True)
        if not silent:
            print(f"Created directory {path}.")
    return path


def save_screenshot(output_path: Path, step: int, ss_byte: bytes):
    with open(output_path / "states" / "screenshots" / f"step_{step}.png", "wb") as f:
        f.write(ss_byte)


def save_page_source(output_path: Path, step: int, source: str):
    with open(
        output_path / "states" / "xmls" / f"step_{step}.xml", "w", encoding="utf-8"
    ) as f:
        f.write(source)


Special_Keys = {
    "KEY_SEMICOLON": ";",
    "KEY_APOSTROPHE": "'",
    "KEY_COMMA": ",",
    "KEY_DOT": ".",
    "KEY_SLASH": "/",
    "KEY_SPACE": " ",
    "KEY_LEFTBRACE": "[",
    "KEY_RIGHTBRACE": "]",
    "KEY_MINUS": "-",
    "KEY_EQUAL": "=",
    "KEY_BACKSLASH": "\\",
    "KEY_GRAVE": "`",
    "KEY_ENTER": "\n",
}

Shift_Keys = {
    "KEY_1": "!",
    "KEY_2": "@",
    "KEY_3": "#",
    "KEY_4": "$",
    "KEY_5": "%",
    "KEY_6": "^",
    "KEY_7": "&",
    "KEY_8": "*",
    "KEY_9": "(",
    "KEY_0": ")",
    "KEY_MINUS": "_",
    "KEY_EQUAL": "+",
    "KEY_LEFTBRACE": "{",
    "KEY_RIGHTBRACE": "}",
    "KEY_SEMICOLON": ":",
    "KEY_APOSTROPHE": '"',
    "KEY_COMMA": "<",
    "KEY_DOT": ">",
    "KEY_SLASH": "?",
    "KEY_BACKSLASH": "|",
    "KEY_GRAVE": "~",
}


class Listener:
    def __init__(
        self,
        instruction: dict,
        output_dir: Path | str = Path("instructions"),
    ) -> None:
        self.logger = logging.getLogger("Listener")
        self.logger.setLevel(logging.INFO)  # Or DEBUG, WARNING, etc.

        # Prevent adding multiple handlers if re-imported
        if not self.logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.instruction = instruction
        self.output_dir = (
            output_dir if isinstance(output_dir, Path) else Path(output_dir)
        )
        self.os = get_os()

        if self.os == "mac":
            self.tap_event = "/dev/input/event1:"
            self.key_event = "/dev/input/event12:"
        elif self.os == "win":
            self.tap_event = "/dev/input/event2:"
            self.key_event = "/dev/input/event13:"
        elif self.os == "linux":
            self.tap_event = "/dev/input/event2:"
            self.key_event = "/dev/input/event13:"
        else:
            raise ValueError("Invalid OS.")

        self._get_window_size()
        self.abs_x_range, self.abs_y_range = self._get_abs_mt_position()

        self.create_output_dirs(self.output_dir)
        self.operations = {
            **self.instruction,
            "steps": [],
        }
        self.complete = False
        self.current_op = dict()
        self.log_message = ""
        self.typing = False
        self.page_source = None
        self.ss_bytes = None
        self.can_save = False
        self.ready_to_listen = False
        self.answer = ""

        # define the current operation
        self.step = 0
        self.action = ""
        self.touch_coord = [0, 0]
        self.lift_coord = [0, 0]
        self.type_text = ""
        self.current_package_name = ""
        self.current_achieved_essential_states = []

    def create_output_dirs(self, output_root: Path) -> None:
        base_name = self.instruction["name"]
        root = Path(output_root)
        existing_indices = [0]
        if root.exists():
            for child in root.iterdir():
                if not child.is_dir():
                    continue
                if child.name.startswith(base_name):
                    existing_indices.append(int(child.name.split("_")[-1]))
        next_index = (max(existing_indices) if existing_indices else 0) + 1
        folder_name = f"{base_name}_{next_index}"
        output_path = check_create_dir(root / folder_name)
        self.output_path = output_path
        check_create_dir(self.output_path / "states" / "screenshots")
        check_create_dir(self.output_path / "states" / "xmls")

    def _get_window_size(self) -> None:
        tem_cmd = ["adb", "shell", "wm", "size"]
        result = subprocess.run(
            tem_cmd, capture_output=True, text=True, check=True, encoding="utf-8"
        )
        result = result.stdout
        pattern = r"(\d+)x(\d+)"
        match = re.search(pattern, result)
        if match:
            self.w = int(match.group(1).strip())
            self.h = int(match.group(2).strip())
        else:
            raise ValueError("Failed to get screen size")

    def _get_abs_mt_position(self) -> tuple[int, int]:
        x_proc = subprocess.Popen(
            [
                "adb",
                "shell",
                "getevent",
                "-il",
                f"{self.tap_event[:-1]}",
                "|",
                "grep",
                "ABS_MT_POSITION_X",
            ],
            stdout=subprocess.PIPE,
            text=True,
        )
        x_out, _ = x_proc.communicate()
        x_out = x_out.strip().split(",")
        x_range = int(x_out[2].strip().split()[-1])
        y_proc = subprocess.Popen(
            [
                "adb",
                "shell",
                "getevent",
                "-il",
                f"{self.tap_event[:-1]}",
                "|",
                "grep",
                "ABS_MT_POSITION_Y",
            ],
            stdout=subprocess.PIPE,
            text=True,
        )
        y_out, _ = y_proc.communicate()
        y_out = y_out.strip().split(",")
        y_range = int(y_out[2].strip().split()[-1])
        return x_range, y_range

    def _get_xml(self) -> str:
        """
        get the xml of the current state of the device

        Returns:
            str: the xml of the current state of the device
        """
        cmd = ["adb", "exec-out", "uiautomator dump /dev/stdout"]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, encoding="utf-8"
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            self.logger.log(logging.ERROR, f"Failed to get XML: {e}")
            return "No XML"

    def _get_current_package_activity(self) -> tuple[str, str]:
        """
        Get the current running package using ADB

        Returns:
            str: the current package name
        """
        cmd = [
            "adb",
            "shell",
            "dumpsys",
            "activity",
            "top",
            "|",
            "grep",
            "ACTIVITY",
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, encoding="utf-8"
            )
            output = result.stdout.strip()
            activities = output.split("ACTIVITY")
            if len(activities) == 2:
                return "com.google.android.apps.nexuslauncher", ".NexusLauncherActivity"
            for activity in activities:
                if "nexus" in activity.lower() or activity == "":
                    continue
                package_activity_str = activity.strip().split(" ")[0]
                package, activity = package_activity_str.split("/")
                return package, activity

        except subprocess.CalledProcessError as e:
            self.logger.log(
                logging.ERROR, f"Can't get current package and activity. {e}"
            )
        except Exception as e:
            self.logger.log(
                logging.ERROR, f"Error when parsing package and activity: {e}"
            )

        return "unknown", "unknown"

    def _get_screenshot(self) -> str:
        """get current screenshot of the device, return a base64 string

        Returns:
            str: a base64 string of the screenshot
        """
        cmd = ["adb", "exec-out", "screencap -p"]
        try:
            result = subprocess.run(cmd, capture_output=True, check=True)
            # png_data = base64.b64encode(result.stdout).decode("utf-8")
            png_data = result.stdout
            return png_data
        except subprocess.CalledProcessError as e:
            self.logger.log(logging.ERROR, f"Failed to get screenshot: {e}")
            return "No screenshot"

    def transform_action(self) -> dict:
        if self.action == "tap":
            return {"action": "tap", "x": self.touch_coord[0], "y": self.touch_coord[1]}
        elif self.action == "swipe":
            return {
                "action": "swipe",
                "x1": self.touch_coord[0],
                "y1": self.touch_coord[1],
                "x2": self.lift_coord[0],
                "y2": self.lift_coord[1],
            }
        elif self.action == "home":
            return {"action": "home"}
        elif self.action == "back":
            return {"action": "back"}
        elif self.action == "enter":
            return {"action": "enter"}
        elif self.action == "type":
            return {"action": "type", "text": self.type_text}
        elif self.action == "end":
            return {"action": "end", "answer": self.answer}
        else:
            raise ValueError(f"Invalid action: {self.action}")

    def save_current_op(self) -> None:
        self.current_op["screenshot"] = f"step_{self.step}.png"
        self.current_op["xml"] = f"step_{self.step}.xml"
        self.current_op["action"] = self.transform_action()
        self.current_op["package"] = self.current_package_name
        self.current_op["activity"] = self.current_activity
        self.current_op["achieved_essential_states"] = (
            self.current_achieved_essential_states
        )

        self.operations["steps"].append(copy.deepcopy(self.current_op))

        self.current_op_msg = [f"{self.transform_action()}"]

    def get_current_info(self) -> None:
        self.page_source = self._get_xml()
        self.ss_bytes = self._get_screenshot()
        self.current_package_name, self.current_activity = (
            self._get_current_package_activity()
        )

    def save_state(self, end: bool = False) -> None:
        save_page_source(self.output_path, self.step, self.page_source)
        save_screenshot(self.output_path, self.step, self.ss_bytes)
        self.save_current_op()
        self.can_save = False
        self.step += 1
        if not end:
            self.get_current_info()
            self.typing = False

    def save_operations(self) -> None:
        with open(self.output_path / "history.json", "w", encoding="utf-8") as f:
            json.dump(self.operations, f, indent=2, ensure_ascii=False)

    def _home(self) -> None:
        cmd = [
            "adb",
            "shell",
            "input",
            "keyevent",
            "3",
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)

    def _all_apps(self) -> None:
        cmd = [
            "adb",
            "shell",
            "input",
            "keyevent",
            "187",
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)

    def _tap(self, x: int, y: int) -> None:
        cmd = ["adb", "shell", "input", "tap", str(x), str(y)]
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

    def _terminate_all_apps(self) -> None:
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

    def process(self) -> None:
        self.proc = subprocess.Popen(
            ["adb", "shell", "getevent", "-l"], stdout=subprocess.PIPE, text=True
        )
        enqueue = False
        coord = {"x": [], "y": []}
        touch_word = ["ABS_MT_TRACKING_ID", "00000000"]
        lift_word = ["ABS_MT_TRACKING_ID", "ffffffff"]
        self.get_current_info()
        self.log_message = "Listener Process Started."
        self.ready_to_listen = True
        self.shift = False
        while (line := self.proc.stdout.readline()) != "":
            line = line.strip().split()
            if line[0].startswith(self.tap_event):
                if line[2] == touch_word[0] and line[3] == touch_word[1]:
                    enqueue = True
                    coord = {"x": [], "y": []}
                elif line[2] == lift_word[0] and line[3] == lift_word[1]:
                    enqueue = False
                    try:
                        if (len(coord["x"]) > 1 or len(coord["y"]) > 1) and (
                            abs(coord["x"][0] - coord["x"][-1]) > 30
                            or abs(coord["y"][0] - coord["y"][-1]) > 30
                        ):
                            self.action = "swipe"
                            self.touch_coord = [coord["x"][0], coord["y"][0]]
                            self.lift_coord = [coord["x"][-1], coord["y"][-1]]
                            self.type_text = ""
                            self.can_save = True
                        else:
                            self.action = "tap"
                            self.touch_coord = [coord["x"][0], coord["y"][0]]
                            self.lift_coord = [coord["x"][0], coord["y"][0]]
                            self.type_text = ""
                            self.can_save = True
                    except IndexError:
                        print("try again")
                        continue

                if enqueue == True:
                    if line[2] == "ABS_MT_POSITION_X":
                        raw_x = int(line[3], base=16)
                        x = int(self.w * float(raw_x) / self.abs_x_range)
                        coord["x"].append(x)
                    if line[2] == "ABS_MT_POSITION_Y":
                        raw_y = int(line[3], base=16)
                        y = int(self.h * float(raw_y) / self.abs_y_range)
                        coord["y"].append(y)

            if line[0].startswith(self.key_event):
                key = line[2]
                if key == "KEY_HOME" and line[3] == "DOWN":
                    self.action = "home"
                    self.touch_coord = [0, 0]
                    self.lift_coord = [0, 0]
                    self.type_text = ""
                    self.can_save = True
                elif key == "KEY_BACK" and line[3] == "DOWN":
                    self.action = "back"
                    self.touch_coord = [0, 0]
                    self.lift_coord = [0, 0]
                    self.type_text = ""
                    self.can_save = True
                elif key == "KEY_ENTER" and line[3] == "DOWN" and not self.typing:
                    self.action = "enter"
                    self.touch_coord = [0, 0]
                    self.lift_coord = [0, 0]
                    self.type_text = ""
                    self.can_save = True
                else:
                    if (key == "KEY_LEFTSHIFT" or key == "KEY_RIGHTSHIFT") and line[
                        3
                    ] == "DOWN":
                        self.shift = True
                    elif (key == "KEY_LEFTSHIFT" or key == "KEY_RIGHTSHIFT") and line[
                        3
                    ] == "UP":
                        self.shift = False

                    if not self.typing and key.startswith("KEY_") and line[3] == "DOWN":
                        self.typing = True
                        if not self.shift and key in Special_Keys:
                            letter = Special_Keys[key]
                            self.type_text = letter
                        elif self.shift and key in Shift_Keys:
                            letter = Shift_Keys[key]
                            self.type_text = letter
                        elif (
                            key == "KEY_LEFTSHIFT"
                            or key == "KEY_BACKSPACE"
                            or key == "KEY_RIGHTSHIFT"
                        ):
                            self.action = "type"
                            self.touch_coord = [0, 0]
                            self.lift_coord = [0, 0]
                        else:
                            letter = key.split("_")[-1]
                            self.type_text = (
                                letter.lower()
                                if not self.shift
                                else letter.capitalize()
                            )
                        self.action = "type"
                        self.touch_coord = [0, 0]
                        self.lift_coord = [0, 0]
                        self.can_save = True
                    elif self.typing and key.startswith("KEY_") and line[3] == "DOWN":
                        if not self.shift and key in Special_Keys:
                            letter = Special_Keys[key]
                            self.type_text += letter
                        elif self.shift and key in Shift_Keys:
                            letter = Shift_Keys[key]
                            self.type_text += letter
                        else:
                            if key == "KEY_LEFTSHIFT" or key == "KEY_RIGHTSHIFT":
                                continue
                            elif key == "KEY_BACKSPACE":
                                if len(self.type_text) == 0:
                                    self.type_text = ""
                                else:
                                    self.type_text = self.type_text[:-1]
                                continue
                            else:
                                letter = key.split("_")[-1]
                                self.type_text += (
                                    letter.lower()
                                    if not self.shift
                                    else letter.capitalize()
                                )
                                self.can_save = True

    def end_process(self) -> None:
        if self.proc:
            self.proc.terminate()
        if self.complete:
            self.action = "end"
            self.touch_coord = [0, 0]
            self.lift_coord = [0, 0]
            self.type_text = ""
            self.save_state(end=True)

    def auto_listen(self) -> None:
        self.process()
        time.sleep(0.1)
        self.log_message = "Listener Process Finished."


class Annotator:
    def __init__(self, args: argparse.Namespace, instructions: list[dict]) -> None:
        self.args = args
        self.instructions = instructions
        self.instruction = {}
        self.inst_idx = 0
        self.listener = None
        self.build_gui()
        self.can_save()

    def build_gui(self) -> None:
        self.window = tk.Tk()
        self.window.title("Annotation Tool")

        self.screen_width = self.window.winfo_screenwidth()
        self.screen_height = self.window.winfo_screenheight()
        self.window_width = int(0.6 * self.screen_width)
        self.window_height = int(2.2 * 0.33 * self.window_width)

        self.window.geometry(f"{self.window_width}x{self.window_height}")
        self.img_width = int(0.3 * self.window_width)
        self.img_height = 2 * self.img_width
        self.img_size = (self.img_width, self.img_height)

        self.left_frame = tk.Frame(self.window, width=self.img_width)
        self.left_frame.grid(row=0, column=0)
        self.left_frame.grid_propagate(0)

        self.canvas = tk.Canvas(
            self.left_frame, width=self.img_width, bg="white", height=self.img_height
        )
        self.canvas.pack()

        right_frame_width = int(0.7 * (self.window_width - self.img_width))
        self.right_frame = tk.Frame(self.window, width=right_frame_width)
        self.right_frame.grid(row=0, column=1, padx=10)
        self.right_frame.grid_propagate(0)

        self.label1 = tk.Label(self.right_frame, text="Instruction:")
        self.label1.pack()

        self.instruction_index_label = tk.Label(
            self.right_frame, text="", font=("Arial", 18)
        )
        self.instruction_index_label.pack(pady=5)

        self.instruction_label = tk.Text(
            self.right_frame,
            font=("Arial", 18),
            wrap=tk.WORD,
            width=right_frame_width // 8,
            height=5,
        )
        self.instruction_label.pack(pady=10)

        self.start_complete_answer_frame = tk.Frame(self.right_frame)
        self.start_complete_answer_frame.pack(pady=10)

        self.next_instruction_button = tk.Button(
            self.start_complete_answer_frame,
            text="Next Instruction",
            command=self.next,
            state=tk.NORMAL,
        )
        self.next_instruction_button.grid(row=0, column=0, padx=10)

        self.start_button = tk.Button(
            self.start_complete_answer_frame,
            text="Start",
            command=self.start,
            state=tk.DISABLED,
        )
        self.start_button.grid(row=0, column=1, padx=10)

        self.save_frame = tk.Frame(self.right_frame)
        self.save_frame.pack(pady=10)

        self.answer_label = tk.Label(self.save_frame, text="Answer:")
        self.answer_label.grid(row=0, column=0, padx=10)
        self.answer_textbox = tk.Text(
            self.save_frame,
            font=("Arial", 14),
            wrap=tk.WORD,
            width=right_frame_width // 17,
            height=1,
        )
        self.answer_textbox.grid(row=0, column=1, padx=10)

        self.save_button = tk.Button(
            self.save_frame, text="Save", command=self.save, state=tk.DISABLED
        )
        self.save_button.grid(row=0, column=2, padx=10)

        self.complete_button = tk.Button(
            self.start_complete_answer_frame,
            text="Complete",
            command=self.complete,
            state=tk.DISABLED,
        )
        self.complete_button.grid(row=0, column=3, padx=10)

        self.state_log_frame = tk.Frame(self.right_frame)
        self.state_log_frame.pack(pady=10)

        # Essential States Checkboxes
        self.essential_states_frame = tk.Label(
            self.state_log_frame,
            text="Essential States",
            width=right_frame_width // 20,
        )
        self.essential_states_frame.grid(row=0, column=0, padx=10)

        self.log_list = tk.Listbox(
            self.state_log_frame, height=20, width=right_frame_width // 13
        )
        self.log_list.grid(row=0, column=1, padx=10)

        self.quit_button = tk.Button(self.right_frame, text="Quit", command=self.quit)
        self.quit_button.pack()

    def _build_checkboxes(self) -> None:
        # Define essential states
        self.essential_states = ast.literal_eval(self.instruction["essential states"])

        # Create checkboxes for each essential state
        self.essential_states_vars = {}
        for i, state in enumerate(self.essential_states):
            var = tk.BooleanVar()
            self.essential_states_vars[state] = var
            checkbox = tk.Checkbutton(
                self.essential_states_frame,
                text=state,
                variable=var,
                anchor=tk.W,
                justify=tk.LEFT,
            )
            checkbox.grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)

    def set_canvas_image(self) -> None:
        if self.listener is not None:
            self.canvas.delete("all")
            ss = self.listener.ss_bytes
            ss = np.frombuffer(ss, np.uint8)
            ss = cv2.imdecode(ss, cv2.IMREAD_COLOR)
            ss = cv2.cvtColor(ss, cv2.COLOR_BGR2RGB)
            self.ss = Image.fromarray(ss)
            img = self.ss.resize(self.img_size)
            self.canvas_image = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, image=self.canvas_image, anchor=tk.NW)
        else:
            self.canvas.delete("all")

    def next(self) -> None:
        if self.inst_idx >= len(self.instructions):
            self.log_list.delete(0, tk.END)
            self.log(f"All instructions ({len(self.instructions)}) are completed.")
            return
        self.instruction = self.instructions[self.inst_idx]
        self.instruction_index_label.config(text=f"Instruction {self.inst_idx}")
        self.instruction_label.delete("1.0", tk.END)
        self.instruction_label.insert("1.0", f"{self.instruction['task']}")
        self.start_button.config(state=tk.NORMAL)
        self.inst_idx += 1

        # Clear existing checkboxes and build new ones for essential states
        self.clear_essential_states()
        self._build_checkboxes()

    def start(self) -> None:
        if self.listener is None:
            self.listener = Listener(self.instruction, self.args.output)
            self.listener._terminate_all_apps()
            self.listener._home()
            self.start_button.config(state=tk.DISABLED)
            self.complete_button.config(state=tk.NORMAL)
            self.next_instruction_button.config(state=tk.DISABLED)
            self.log_list.delete(0, tk.END)
            self.listen_thread = threading.Thread(target=self.listener.auto_listen)
            self.listen_thread.start()
            time.sleep(1)
            while not self.listener.ready_to_listen:
                time.sleep(0.5)
            self.set_canvas_image()
            self.log(self.listener.log_message)
            self.log("Now Start!")

    def complete(self) -> None:
        if self.listener is not None:
            self.listener.action = "end"
            self.listener.complete = True

            # Get selected essential states
            selected_states = []
            for state, var in self.essential_states_vars.items():
                if var.get():
                    selected_states.append(state)

            # Add essential states to the listener's data
            self.listener.current_achieved_essential_states = selected_states

            # get answer
            answer = self.answer_textbox.get("1.0", tk.END).strip()
            if answer == "":
                answer = "Operation successful."
            self.listener.answer = answer

            self.listener.end_process()
            self.log(f"Step {self.listener.step - 1}:")
            for msg in self.listener.current_op_msg:
                self.log("    " + msg)
            self.log(f"    Save State {self.listener.step - 1}")
            instruction = self.instruction_label.get("1.0", tk.END).strip()
            self.listener.save_operations()
            time.sleep(1)
            self.log(self.listener.log_message)
            self.log(f"Instruction is completed. Saved at {self.listener.output_path}.")

            self.start_button.config(state=tk.NORMAL)
            self.instruction_label.delete("1.0", tk.END)
            self.complete_button.config(state=tk.DISABLED)
            self.save_button.config(state=tk.DISABLED)
            self.next_instruction_button.config(state=tk.NORMAL)

            del self.listener
            self.listener = None

    def clear_essential_states(self) -> None:
        """remove all essential states checkboxes"""
        for widget in self.essential_states_frame.winfo_children():
            widget.destroy()

        self.essential_states_vars = {}

    def save(self) -> None:
        if self.listener is not None:

            # Get selected essential states
            selected_states = []
            for state, var in self.essential_states_vars.items():
                if var.get():
                    selected_states.append(state)

            # Add essential states to the listener's data
            self.listener.current_achieved_essential_states = selected_states

            self.listener.save_state()
            self.set_canvas_image()
            self.log(f"Step {self.listener.step - 1}:")
            for msg in self.listener.current_op_msg:
                self.log("    " + msg)
            self.log(f"    Save State {self.listener.step - 1}")
            if selected_states:
                self.log(f"    Essential States: {', '.join(selected_states)}")

            # Clear all checkboxes after saving
            for var in self.essential_states_vars.values():
                var.set(False)

    def can_save(self) -> None:
        if self.listener is not None:
            if self.listener.can_save:
                self.save_button.config(state=tk.NORMAL)
            else:
                self.save_button.config(state=tk.DISABLED)
        else:
            self.save_button.config(state=tk.DISABLED)
        self.window.after(100, self.can_save)

    def log(self, msg: str) -> None:
        self.log_list.insert(tk.END, msg)

    def run(self) -> None:
        self.window.mainloop()

    def quit(self) -> None:
        if self.listener is not None:
            self.listener.action = "end"
            self.listener.complete = True
            self.listener.end_process()
            self.listener.save_operations()
            time.sleep(1)
            shutil.rmtree(self.listener.output_path.as_posix())
            del self.listener
        self.window.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Annotate instructions.")
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="human_annotations",
        help="Output directory.",
    )
    parser.add_argument(
        "--udid",
        "-d",
        type=str,
        default="emulator-5554",
        help='UDID of the device, you can obtain with "adb devices -l"',
    )
    parser.add_argument(
        "--task", "-j", required=True, help="Path to the task jsonl file."
    )
    args = parser.parse_args()

    with open(args.task, "r") as f:
        tasks = [json.loads(line) for line in f]

    anno = Annotator(args, tasks)
    anno.run()
