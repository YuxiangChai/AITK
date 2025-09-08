import json
from pathlib import Path

import numpy as np
from PIL import Image

import aitk.utils.image_utils as image_utils
from aitk import aitk_logger, check_create_dir


def to_puzzle(root_dir: str) -> None:
    root_dir = Path(root_dir)
    if not (root_dir / "history.json").exists():
        aitk_logger.info(
            f"history.json not found in {root_dir}. Skip to create puzzle."
        )
        return

    with open(root_dir / "history.json", "r", encoding="utf-8") as f:
        history = json.load(f)

    puzzle_dir = check_create_dir(root_dir / "puzzle")

    single_annotated_images = []

    screenshot_dir = root_dir / "states" / "screenshots"

    for screenshot_file in screenshot_dir.iterdir():
        index = int(screenshot_file.stem.split("_")[1])
        img_np = np.array(Image.open(screenshot_file).convert("RGB"))
        action = history["steps"][index]["action"]
        action_type_str = action["action"]
        if action_type_str == "tap":
            click_position = (action["x"], action["y"])
        else:
            click_position = None
        if action_type_str == "swipe":
            swipe_position = (
                action["x1"],
                action["y1"],
                action["x2"],
                action["y2"],
            )
        else:
            swipe_position = None

        action_detail = {k: v for k, v in action.items() if k != "action"}
        action_detail_str = str(action_detail)
        annotated_img = image_utils.visualize_single_action(
            img_np,
            action_type_str,
            action_detail_str,
            click_position,
            swipe_position,
        )
        single_annotated_images.append(annotated_img)

    images_per_row = 4
    gap = 50  # 图像间的空隙像素
    slide_step = 2  # 滑动窗口步长

    # 滑动窗口拼接
    num_windows = (
        (len(single_annotated_images) - images_per_row) // slide_step + 1
        if len(single_annotated_images) >= images_per_row
        else 0
    )

    for i in range(num_windows + 1):

        window_imgs = single_annotated_images[
            i * slide_step : i * slide_step + images_per_row
        ]

        if i == num_windows:
            if len(window_imgs) == 3:
                window_imgs = single_annotated_images[-4:]
            else:
                break

        # 计算拼接后图片的尺寸
        widths, heights = zip(*(img.size for img in window_imgs))
        total_width = sum(widths) + gap * (len(window_imgs) - 1)
        max_height = max(heights)

        # 创建新图像
        new_img = Image.new("RGB", (total_width, max_height), (255, 255, 255))
        x_offset = 0
        for img in window_imgs:
            new_img.paste(img, (x_offset, 0))
            x_offset += img.width + gap

        # 保存
        out_name = f"puzzle_{i:02d}.png"
        new_img.save(puzzle_dir / out_name)
