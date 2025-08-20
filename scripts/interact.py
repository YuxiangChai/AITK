import argparse
import time
from pathlib import Path

import yaml

from aitk import aitk_logger, check_create_dir
from aitk.utils.controller import Controller
from aitk.utils.register import register_tasks, register_translator

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", type=str, default="configs/controller.yaml")
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    translator = register_translator(config["translator"])
    tasks = register_tasks(config["experiment"]["tasks"])

    save_root_dir = Path(config["experiment"]["save_root_dir"])
    save_root_dir = save_root_dir / config["experiment"]["name"]
    check_create_dir(save_root_dir)

    device_udid = config["device"]["udid"]
    appium_port = config["device"]["appium_port"]
    controller = Controller(config, appium_port, device_udid)

    for task in tasks:
        task_str = task["task"]  # task description
        save_dir = save_root_dir / task["name"]  # task file name
        check_create_dir(save_dir)

        max_steps = (
            task["max_steps"] if "max_steps" in task else 50
        )  # default max steps is 50 so that a task won't run forever

        state_save_dir = check_create_dir(save_dir / "states")

        controller.set_task_eval(**task)
        controller.save_state(state_save_dir)  # save the initial state

        if config["experiment"]["screen_record"]:
            controller.start_record(config["experiment"]["record_resolution"])

        while True:
            if controller.step >= max_steps:
                break

            if controller.step == 0:
                aitk_logger.info(
                    f"Task started: {task['name']} ----- {task['task']} -----"
                )
            else:
                aitk_logger.info(f"Step {controller.step}: ")

            state = controller.get_state()
            history = controller.get_history()

            # agent communication
            agent_response = translator.to_agent(task_str, state, history)
            aitk_logger.info(f"Agent response: {agent_response}")
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

            controller.save_state(state_save_dir)

        if config["experiment"]["screen_record"]:
            controller.stop_save_record(save_dir)

        try:
            controller.save_history(save_dir)
            aitk_logger.info(f"Task saved: {task['name']}")
        except Exception as e:
            aitk_logger.error(f"Task save failed: {e}")

        aitk_logger.info(f"Task finished: {task['name']}")
