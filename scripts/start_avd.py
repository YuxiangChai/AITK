import argparse
import subprocess

from aitk.utils.avd_manager import AVDManager

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--avd-name",
        type=str,
        default="A3V2",
        help="The name of the base AVD to duplicate.",
    )
    args = parser.parse_args()

    avd_manager = AVDManager()
    avd_manager.duplicate_avd(args.avd_name)

    cmd = ["emulator", "-avd", args.avd_name, "-no-snapshot"]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
