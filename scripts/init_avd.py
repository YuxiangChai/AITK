import argparse
import subprocess

from aitk.utils.avd_manager import AVDManager

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--avd-name", "-a", type=str, default="A3V2")
    args = parser.parse_args()

    avd_manager = AVDManager()
    avd_manager.modify_origin_avd(args.avd_name)

    cmd = ["emulator", "-avd", args.avd_name]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
