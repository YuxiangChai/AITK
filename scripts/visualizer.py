import argparse
from pathlib import Path

from tqdm import tqdm

from aitk.utils.image_utils import to_puzzle

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", "-d", type=str, required=True)
    args = parser.parse_args()

    data_root = Path(args.data_dir)
    dirs = list(data_root.iterdir())
    for task_dir in tqdm(dirs):
        if task_dir.is_dir():
            to_puzzle(task_dir)
