import json
import math
import os
import textwrap
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from aitk import check_create_dir


def visualize_click_opencv(
    img_np: np.ndarray,
    click_pos: Tuple[int, int],
    circle_radius: int = 35,
    square_size: int = 50,
    alpha: float = 0.7,
) -> Image:
    """
    This function visualizes the click position with a red circle and a green square frame,
    and labels it with a "C" at the top-right corner of the square.
    """
    # Convert RGB to BGR for OpenCV processing
    img = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    # Create an overlay image
    overlay = img.copy()
    x, y = click_pos

    # Draw a red circle with a white border. OpenCV uses BGR, so red is (0, 0, 255)
    cv2.circle(overlay, (x, y), circle_radius, (0, 0, 255), 6)

    # Draw a green square frame around the red circle
    top_left = (x - square_size, y - square_size)
    bottom_right = (x + square_size, y + square_size)
    cv2.rectangle(overlay, top_left, bottom_right, (0, 255, 0), 8)

    # Combine the overlay with the base image using alpha transparency
    img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

    # Convert the final result back to RGB format for PIL
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    return Image.fromarray(img_rgb)


def visualize_swipe_opencv(
    img_np: np.ndarray,
    swipe_pos: Tuple[int, int, int, int],
) -> Image:
    """
    Visualize a swipe gesture as a red arrow from (x1, y1) to (x2, y2).
    """
    # Convert RGB to BGR for OpenCV processing
    img = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    # Create an overlay image
    overlay = img.copy()
    x1, y1, x2, y2 = swipe_pos

    # Draw a red arrow from (x1, y1) to (x2, y2)
    arrow_color = (0, 0, 255)  # Red in BGR
    arrow_thickness = 6  # Smaller thickness
    arrow_tip_length = 0.15  # Smaller arrow tip

    cv2.arrowedLine(
        overlay,
        (int(x1), int(y1)),
        (int(x2), int(y2)),
        arrow_color,
        thickness=arrow_thickness,
        tipLength=arrow_tip_length,
        line_type=cv2.LINE_AA,
    )

    # Combine the overlay with the base image using alpha transparency
    alpha = 0.7
    img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

    # Convert the final result back to RGB format for PIL
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    return Image.fromarray(img_rgb)


def create_frame(image: Image, label: str) -> Image:
    """创建带边框和标签的子图"""
    BORDER_WIDTH = 14  # 设置边框宽度
    LABEL_HEIGHT = 140  # 增加标签高度，避免与图像重叠
    frame_w = image.width + BORDER_WIDTH * 2
    frame_h = image.height + BORDER_WIDTH * 2 + LABEL_HEIGHT  # 包括标签的高度

    # 创建画布（白色背景）
    frame = Image.new("RGB", (frame_w, frame_h), "white")
    draw = ImageDraw.Draw(frame)

    # 绘制四周的边框
    draw.rectangle(
        [
            (BORDER_WIDTH, LABEL_HEIGHT),
            (frame_w - BORDER_WIDTH, frame_h - BORDER_WIDTH),
        ],
        outline="#808080",  # 灰色边框
        width=BORDER_WIDTH,
    )

    # 将原始图像粘贴到框架中
    frame.paste(image, (BORDER_WIDTH, LABEL_HEIGHT + BORDER_WIDTH))

    # 添加标签文本
    try:
        font = ImageFont.truetype("Arial.ttf", 120)
    except:
        font = ImageFont.load_default(120)

    # 标签文本居中
    text_bbox = draw.textbbox((0, 0), label, font=font)
    text_x = (frame_w - (text_bbox[2] - text_bbox[0])) // 2
    draw.text((text_x, 10), label, fill="#404040", font=font)

    return frame


def _calculate_characters_per_line(image_width, font):
    # Measure the width of a sample of characters
    sample_text = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    total_width = sum(
        font.getbbox(char)[2] - font.getbbox(char)[0] for char in sample_text
    )
    if total_width == 0:
        return 20  # Fallback
    average_char_width = total_width / len(sample_text)

    # Calculate the number of characters that fit in one line
    characters_per_line = image_width // average_char_width
    return int(characters_per_line)


def _add_strip_with_text(
    image: Image, text_segments: list, font_size=60, line_spacing=10
) -> Image:
    width, height = image.size

    try:
        font = ImageFont.truetype("Arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default(size=font_size)

    # --- New logic to handle multi-color lines ---

    # 1. Group segments into logical lines
    logical_lines = []
    current_line_segments = []
    for segment in text_segments:
        text = segment["text"]
        if text.startswith("\n"):
            if current_line_segments:
                logical_lines.append(current_line_segments)
            current_line_segments = [
                {"text": text.lstrip("\n"), "color": segment["color"]}
            ]
        else:
            current_line_segments.append(segment)
    if current_line_segments:
        logical_lines.append(current_line_segments)

    # 2. Calculate layout for all lines
    characters_per_line = _calculate_characters_per_line(width, font)
    all_wrapped_lines = []
    total_text_height = 0
    dummy_draw = ImageDraw.Draw(image)

    for line_segments in logical_lines:
        full_line_text = "".join([s["text"] for s in line_segments])
        wrapped_lines = textwrap.wrap(full_line_text, width=characters_per_line)
        all_wrapped_lines.append(wrapped_lines)
        for line in wrapped_lines:
            text_bbox = dummy_draw.textbbox((0, 0), line, font=font)
            total_text_height += text_bbox[3] - text_bbox[1] + line_spacing

    # 3. Create the new image with the correctly sized strip
    strip_height = total_text_height + 20  # Add padding
    blue_line_height = 10
    new_height = height + blue_line_height + strip_height
    new_image = Image.new("RGB", (width, int(new_height)), "white")
    new_image.paste(image, (0, 0))
    draw = ImageDraw.Draw(new_image)

    # 4. Draw the blue line and the text
    # draw.rectangle([(0, height), (width, height + blue_line_height)], fill="blue")
    y_text = height + blue_line_height + 10

    for i, wrapped_lines in enumerate(all_wrapped_lines):
        line_segments = logical_lines[i]
        char_cursor = 0
        full_line_text = "".join([s["text"] for s in line_segments])

        for line_text in wrapped_lines:
            # Center the line
            line_bbox = draw.textbbox((0, 0), line_text, font=font)
            line_width = line_bbox[2] - line_bbox[0]
            x_text = (width - line_width) // 2

            # Draw each part of the line with its color
            line_char_ptr = 0
            while line_char_ptr < len(line_text):
                # Find which segment the global cursor is in
                segment_start_char = 0
                for segment in line_segments:
                    segment_end_char = segment_start_char + len(segment["text"])
                    if char_cursor < segment_end_char:
                        # This is the correct segment
                        chars_to_draw_from_segment = segment_end_char - char_cursor
                        chars_to_draw_on_line = len(line_text) - line_char_ptr

                        draw_len = min(
                            chars_to_draw_from_segment, chars_to_draw_on_line
                        )
                        text_piece = line_text[line_char_ptr : line_char_ptr + draw_len]

                        draw.text(
                            (x_text, y_text),
                            text_piece,
                            font=font,
                            fill=segment["color"],
                        )

                        piece_bbox = draw.textbbox((0, 0), text_piece, font=font)
                        x_text += piece_bbox[2] - piece_bbox[0]

                        char_cursor += draw_len
                        line_char_ptr += draw_len

                    segment_start_char = segment_end_char

            line_height_bbox = draw.textbbox((0, 0), line_text, font=font)
            y_text += line_height_bbox[3] - line_height_bbox[1] + line_spacing

    return new_image


def _wrap_action_text(action, action_detail):
    text_segments = [
        {"text": "Action:", "color": "red"},
        {"text": f" {action}", "color": "black"},
        {"text": "\nDetail:", "color": "red"},
        {"text": f" {action_detail}", "color": "black"},
    ]
    return text_segments


def _create_layout(image_folder: str, task_title: str, output_path: str):
    """
    将文件夹中的所有图片合并成一张大图。
    """
    if not os.path.exists(image_folder):
        print(f"Error: Image folder not found: {image_folder}")
        return

    image_files = sorted(
        [f for f in os.listdir(image_folder) if f.endswith(".png")],
        key=lambda f: int(f.split("_")[1].split(".")[0]),
    )
    if not image_files:
        print(f"Error: No images found in {image_folder}")
        return

    # Load first image to get dimensions
    first_image = Image.open(os.path.join(image_folder, image_files[0]))
    img_width, img_height = first_image.size
    first_image.close()

    # Calculate layout
    num_images = len(image_files)
    cols = math.ceil(math.sqrt(num_images))
    rows = math.ceil(num_images / cols)

    # Font settings
    try:
        title_font = ImageFont.truetype("Arial.ttf", 80)
        number_font = ImageFont.truetype("Arial.ttf", 60)
    except IOError:
        title_font = ImageFont.load_default(size=80)
        number_font = ImageFont.load_default(size=60)

    # Calculate title height
    task_title_text = task_title
    temp_img = Image.new("RGB", (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    # Set max title width to be slightly less than the image content area
    max_title_width = cols * img_width * 0.95

    # --- New robust text wrapping logic ---
    words = task_title_text.split(" ")
    wrapped_text = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        # Use textlength for more accurate width calculation
        line_width = temp_draw.textlength(test_line, font=title_font)
        if line_width <= max_title_width:
            current_line = test_line
        else:
            wrapped_text.append(current_line)
            current_line = word
    if current_line:
        wrapped_text.append(current_line)
    # --- End of new logic ---

    line_height = title_font.getbbox("A")[3] - title_font.getbbox("A")[1]
    top_padding, bottom_padding, line_spacing = 60, 60, 30
    title_height = (
        (len(wrapped_text) * line_height)
        + ((len(wrapped_text) - 1) * line_spacing if len(wrapped_text) > 1 else 0)
        + top_padding
        + bottom_padding
    )

    # Create canvas with horizontal padding for the title
    horizontal_padding = int(cols * img_width * 0.025)
    canvas_width = cols * img_width + horizontal_padding * 2
    canvas_height = rows * img_height + title_height
    canvas_image = Image.new("RGB", (int(canvas_width), int(canvas_height)), "white")
    draw = ImageDraw.Draw(canvas_image)

    # Draw title centered within the full canvas width
    y_position = top_padding
    for line in wrapped_text:
        line_bbox = draw.textbbox((0, 0), line, font=title_font)
        line_width = line_bbox[2] - line_bbox[0]
        x_position = (canvas_width - line_width) // 2
        draw.text((x_position, y_position), line, font=title_font, fill="black")
        y_position += line_height + line_spacing

    # Paste images
    for i, image_file in enumerate(image_files):
        row, col = i // cols, i % cols
        x_base = col * img_width + horizontal_padding
        y_base = row * img_height + title_height
        img = Image.open(os.path.join(image_folder, image_file))
        canvas_image.paste(img, (int(x_base), int(y_base)))
        img.close()

        # Add number to top-left corner with taller background
        number_text = str(i + 1)
        number_bbox = draw.textbbox((0, 0), number_text, font=number_font)
        text_w = number_bbox[2] - number_bbox[0]
        text_h = number_bbox[3] - number_bbox[1]
        bg_x_padding = 10
        bg_y_padding = 12  # Increased vertical padding
        bg_rect = (
            x_base + 5,
            y_base + 5,
            x_base + 5 + text_w + bg_x_padding * 2,
            y_base + 15 + text_h + bg_y_padding * 2,
        )
        overlay = Image.new("RGBA", canvas_image.size, (255, 255, 255, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle(bg_rect, fill=(255, 255, 255, 180))
        canvas_image = Image.alpha_composite(
            canvas_image.convert("RGBA"), overlay
        ).convert("RGB")
        draw = ImageDraw.Draw(canvas_image)
        draw.text(
            (x_base + 5 + bg_x_padding, y_base + 5 + bg_y_padding),
            number_text,
            font=number_font,
            fill="red",
        )

    # Save canvas image
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    canvas_image.save(output_path)


def visualize_single_action(
    img: np.ndarray,
    action_type: str = None,
    action_detail: str = None,
    click_position: Optional[Tuple[int, int]] = None,
    swipe_position: Optional[Tuple[int, int]] = None,
    add_text: bool = True,
) -> Image:
    """
    为单个动作生成可视化图像，包括点击位置标记和动作描述。

    Args:
        img: 输入图像数组
        action_type: 动作类型
        action_detail: 动作详情
        click_position: 可选的点击位置坐标

    Returns:
        带有动作标记和描述的PIL Image
    """

    base_img = Image.fromarray(img) if isinstance(img, np.ndarray) else img
    if click_position is not None:
        base_img = visualize_click_opencv(img, click_position)
    if swipe_position is not None:
        base_img = visualize_swipe_opencv(img, swipe_position)

    # 添加动作描述
    if add_text:
        text_segments = _wrap_action_text(action_type, action_detail)
        final_img = _add_strip_with_text(base_img, text_segments)
    else:
        final_img = base_img

    return final_img


def combine_all_screens(root_dir: str) -> None:
    root_dir = Path(root_dir)
    if not (root_dir / "history.json").exists():
        print(f"history.json not found in {root_dir}. Skip.")
        return

    with open(root_dir / "history.json", "r", encoding="utf-8") as f:
        history = json.load(f)

    single_annotated_images = []

    screenshot_dir = root_dir / "states" / "screenshots"

    all_sc = list(screenshot_dir.iterdir())
    all_sc.sort(key=lambda x: int(x.stem.split("_")[1]))

    for screenshot_file in all_sc:
        index = int(screenshot_file.stem.split("_")[1])
        img_np = np.array(Image.open(screenshot_file).convert("RGB"))
        action = history["steps"][index]["action"]
        action_type_str = action["action"]
        if action_type_str == "tap" or action_type_str == "long_press":
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
        annotated_img = visualize_single_action(
            img_np,
            action_type_str,
            action_detail_str,
            click_position,
            swipe_position,
        )
        single_annotated_images.append(annotated_img)

    if not single_annotated_images:
        return

    images_per_row = 4
    gap = 50  # Gap between images in pixels

    # Calculate grid dimensions based on the maximum width and height to ensure alignment
    max_w = max(img.width for img in single_annotated_images)
    max_h = max(img.height for img in single_annotated_images)

    num_rows = math.ceil(len(single_annotated_images) / images_per_row)

    total_width = images_per_row * max_w + (images_per_row - 1) * gap
    total_height = num_rows * max_h + (num_rows - 1) * gap

    # Create the large canvas
    new_img = Image.new("RGB", (total_width, total_height), "white")

    for i, img in enumerate(single_annotated_images):
        row = i // images_per_row
        col = i % images_per_row

        x = col * (max_w + gap)
        y = row * (max_h + gap)

        new_img.paste(img, (x, y))

    new_img.save(root_dir / "traj_combined.png")


def round_by_factor(number: int, factor: int) -> int:
    """Returns the closest integer to 'number' that is divisible by 'factor'."""
    return round(number / factor) * factor


def ceil_by_factor(number: int, factor: int) -> int:
    """Returns the smallest integer greater than or equal to 'number' that is divisible by 'factor'."""
    return math.ceil(number / factor) * factor


def floor_by_factor(number: int, factor: int) -> int:
    """Returns the largest integer less than or equal to 'number' that is divisible by 'factor'."""
    return math.floor(number / factor) * factor


def smart_resize(
    height: int, width: int, factor: int = 28, max_pixels: int = 2352000
) -> tuple[int, int, float]:
    beta = 1.0
    h_bar = max(factor, round_by_factor(height, factor))
    w_bar = max(factor, round_by_factor(width, factor))
    if h_bar * w_bar > max_pixels:
        beta = math.sqrt((height * width) / max_pixels)
        h_bar = max(factor, floor_by_factor(height / beta, factor))
        w_bar = max(factor, floor_by_factor(width / beta, factor))
    h_beta = h_bar / height
    w_beta = w_bar / width
    return h_bar, w_bar, h_beta, w_beta
