import subprocess
import sys

from aitk.utils.avd_manager import AVDManager

if __name__ == "__main__":
    avd_manager = AVDManager()
    avd_manager.modify_origin_avd()

    cmd = ["emulator", "-avd", "A3V2"]
    subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
