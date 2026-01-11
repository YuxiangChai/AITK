"""
Evaluation generation script.
Generates evaluation data and optional responses using a VLM judge for agent trajectories.
"""

import argparse
import ast
import asyncio
import base64
import json
import logging
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import yaml
from openai import AsyncOpenAI, OpenAI
from PIL import Image
from tqdm import tqdm

from aitk.utils.image_utils import visualize_single_action

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

FACTOR = 0.54997

JUDGE_PROMPT_TEMPLATE = """
You are a professional judger for the following task.
Description: A mobile GUi agent has finished a trajectory of screenshots given an overall task instruction. Since it is very hard to directly judge whether the trajectory completes the instruction successfully, we propose an idea of "essential states". An essential state is either a state or an action that must be achieved so that the overall instruction can be finished successfully. For example, the task "In the 'Shopping' list of Tasks app, locate the task 'Buy Milk' and mark it as completed." has two essential states: (1) 'Shopping' list is opened and (2) Task 'Buy Milk' is marked as completed. Other essential states might be "the first result is selected", which is an action. Now what you need to do is simplified to judge whether an essential state is achieved based on two screenshots and an action. The first screenshot is taken before the action is executed. The second screenshot is taken after the action is executed. You need to judge whether the essential state is achieved after the action is taken (i.e., based on the action and the second screenshot, or the transition from the first screenshot to the second one). If the action is "click" or "tap", a green circle in a red square will be marked on the first screenshot. If the action is swipe, a red arrow will be marked on the screenshot indicating the finger movement. Other actions will not be marked on the screenshot.
The action format is like:
 - {"action": "open", "app": "youtube"} - {"action": "tap", "x": 100, "y": 100} - {"action": "long_press", "x": 100, "y": 100, "duration": 1000 (optional, default to 1000ms)} - {"action": "swipe", "x1": 100, "y1": 100, "x2": 200, "y2": 200, "duration": 1000 (optional, default to 1000ms)} - {"action": "type", "text": "hello"} - {"action": "enter"} - {"action": "back"} - {"action": "home"} - {"action": "wait", "time": 1 (optional, default to 3 second)} - {"action": "end", "answer": "answer to the user query (default to empty string)"}

Input:
 - screenshot before action <image>
 - screenshot after action <image>
 - action {action}
 - essential state: {es}
 - overall instruction: {task}

From human perspective, there are mainly three ways to judge:
 - Analyze the second screenshot elements, such as text, toggle status, etc. For example, the essential state "'Shopping' list is opened" can be judged by whether the second screenshot is displaying a list, which has a text element of "Shopping".
 - Analyze the action itself and its result. For example, the essential state "First song in the playlist is played" can be judged by whether the click action is marked at the correct coordinate of the first song on the first screenshot. Also, if the action is "end", an answer might be provided in the action string if the overall task instruction is an information query. For example, if the instruction is "Navigate to CNN's Science section and check the top headline news. When was it published?", an essential state is "The publish time is answered". To judge this essential state, you need to analyze the second screenshot, which may have the information such as the publish time. You need to judge whether the answer is correct based on the information you see. IMPORTANT: only when the action is "end" and the "answer" parameter is provided in the action json, you need to judge such essential states. If the screenshot has the information but the action json is not "end", such essential states are considered not achieved.
 - Analyze the transition of two screenshots. Sometimes, even if the action is correct, the second screenshot will remain the same as the first screenshot, which might be caused by many bugs we do not know. If the transition to second screenshot does not corresponds to the essential state, then it should be considered failed.

Output:
You should follow the format strictly:
your thinking process here, following the three ways above
<answer>only yes or no (whether the essential state is achieved, should be consistant with your thinking)<answer>
"""


def construct_prompt(
    task_instruction: str,
    essential_state: str,
    action: Dict[str, Any],
    image_current: str,
    image_next: str,
) -> Dict[str, Any]:
    """Constructs the prompt and inputs for the judge model."""

    prompt_text = (
        JUDGE_PROMPT_TEMPLATE.replace("{action}", str(action))
        .replace("{es}", essential_state)
        .replace("{task}", task_instruction)
    )

    return {"problem": prompt_text, "images": [image_current, image_next]}


def process_trajectories(data_dir: Path) -> List[Dict[str, Any]]:
    """Iterates through data directory and constructs evaluation items."""
    eval_items = []

    # Handle both single trajectory directory and root directory cases
    if (data_dir / "history.json").exists():
        traj_dirs = [data_dir]
    else:
        traj_dirs = [d for d in data_dir.iterdir() if d.is_dir()]

    for traj_dir in tqdm(traj_dirs, desc="Processing Trajectories"):
        # For open-source, we don't arbitrarily skip folder names unless configured.

        history_path = traj_dir / "history.json"
        if not history_path.exists():
            continue

        try:
            with open(history_path, "r") as f:
                history = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load history for {traj_dir}: {e}")
            continue

        task_name = history["name"]

        task_instruction = history["task"]
        try:
            # Parse essential states
            es_raw = history.get("essential states", "[]")
            if isinstance(es_raw, str):
                essential_states = ast.literal_eval(es_raw)
            else:
                essential_states = es_raw
        except Exception:
            logger.error(f"Error parsing essential states for {task_name}")
            continue

        steps = history.get("steps", [])

        for i, step in enumerate(steps):
            action = step["action"]
            if action["action"] == "tap" or action["action"] == "long_press":
                x0, y0 = action["x"], action["y"]
                click_position = (x0, y0)
                swipe_position = None
                x_new, y_new = x0 * FACTOR, y0 * FACTOR
                action = {"action": action["action"], "x": x_new, "y": y_new}
            elif action["action"] == "swipe":
                x1, y1, x2, y2 = action["x1"], action["y1"], action["x2"], action["y2"]
                swipe_position = (x1, y1, x2, y2)
                click_position = None
                x1_new, y1_new = x1 * FACTOR, y1 * FACTOR
                x2_new, y2_new = x2 * FACTOR, y2 * FACTOR
                action = {
                    "action": action["action"],
                    "x1": x1_new,
                    "y1": y1_new,
                    "x2": x2_new,
                    "y2": y2_new,
                }
            else:
                click_position = None
                swipe_position = None
            raw_image_path = traj_dir / "states" / "screenshots" / step["screenshot"]
            raw_image = np.array(Image.open(raw_image_path))
            marked_img = visualize_single_action(
                raw_image,
                click_position=click_position,
                swipe_position=swipe_position,
                add_text=False,
            )
            current_image_path = traj_dir / "marked_screenshots" / f"step_{i}.png"
            if not (traj_dir / "marked_screenshots").exists():
                (traj_dir / "marked_screenshots").mkdir(parents=True, exist_ok=True)
            marked_img.save(current_image_path)

            if i + 1 < len(steps):
                next_step = steps[i + 1]
            else:
                next_step = step

            next_image_name = next_step["screenshot"]

            next_image_path = traj_dir / "states" / "screenshots" / next_image_name

            if not current_image_path.exists() or not next_image_path.exists():
                continue

            for es in essential_states:
                eval_item = construct_prompt(
                    task_instruction=task_instruction,
                    essential_state=es,
                    action=step["action"],
                    image_current=str(current_image_path.absolute()),
                    image_next=str(next_image_path.absolute()),
                )

                eval_item["metadata"] = {
                    "task_name": task_name,
                    "step_index": i,
                    "essential_state": es,
                    "traj_dir": str(traj_dir),
                }

                eval_items.append(eval_item)

    return eval_items


def encode_image(image_path: str) -> str:
    """Encodes an image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


async def inference_one(
    client: AsyncOpenAI,
    model: str,
    item: Dict[str, Any],
    semaphore: asyncio.Semaphore,
) -> Dict[str, Any]:
    """Runs inference for a single item."""
    async with semaphore:
        try:
            prompt_text = item["problem"]
            image_paths = item["images"]

            # Construct messages content
            content = []

            # Split the prompt by <image> tag
            parts = prompt_text.split("<image>")

            for i, part in enumerate(parts):
                if part:
                    content.append({"type": "text", "text": part})

                # Add image after the text part, if there is a corresponding image
                if i < len(image_paths):
                    base64_image = encode_image(image_paths[i])
                    mime_type, _ = mimetypes.guess_type(image_paths[i])
                    if mime_type is None:
                        mime_type = "image/png"  # Default to png

                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            },
                        }
                    )

            messages = [{"role": "user", "content": content}]

            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1024,  # Adjust as needed
                temperature=0.0,
            )

            item["response"] = response.choices[0].message.content
            return item
        except Exception as e:
            logger.error(f"Error processing item: {e}")
            item["error"] = str(e)
            return item


async def run_inference_async(
    eval_items: List[Dict[str, Any]], config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Async main function for inference."""
    eval_config = config.get("eval", {})
    base_url = eval_config.get("base_url")
    model = eval_config.get("model")
    api_key = eval_config.get("api_key")
    batch_size = eval_config.get("batch_size", 8)

    if not base_url or not model:
        logger.error("Base URL and Model must be provided in config")
        return eval_items

    client = AsyncOpenAI(base_url=base_url, api_key=api_key)
    semaphore = asyncio.Semaphore(batch_size)

    tasks = []
    for item in eval_items:
        task = asyncio.create_task(inference_one(client, model, item, semaphore))
        tasks.append(task)

    results = []
    for f in tqdm(
        asyncio.as_completed(tasks), total=len(tasks), desc="Running Inference"
    ):
        results.append(await f)

    return results


def run_inference(
    eval_items: List[Dict[str, Any]], config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Runs VLLM inference on the constructed items."""
    return asyncio.run(run_inference_async(eval_items, config))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Detailed evaluation generator for Agent Trajectories"
    )
    parser.add_argument(
        "--config", "-c", type=str, required=True, help="Path to config YAML"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="eval_results.jsonl",
        help="Output file name",
    )
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    data_dir = Path(config.get("data_dir", "."))

    # Process Data
    logger.info(f"Processing trajectories in {data_dir}")
    eval_items = process_trajectories(data_dir)
    logger.info(f"Generated {len(eval_items)} evaluation items")

    with open(data_dir / "eval_file.json", "w") as f:
        json.dump(eval_items, f, indent=2)

    # Run Inference
    if config.get("eval", {}).get("base_url"):
        logger.info("Starting inference...")
        eval_items = run_inference(eval_items, config)
    else:
        logger.info("Skipping inference (no base_url configured)")

    output_path = Path(args.output)
    with open(data_dir / output_path, "w") as f:
        for item in eval_items:
            f.write(json.dumps(item) + "\n")
    logger.info(f"Saved evaluation items to {output_path}")
