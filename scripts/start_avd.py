import subprocess

from aitk.utils.avd_manager import AVDManager

if __name__ == "__main__":
    avd_name = "A3V2_dup"
    avd_manager = AVDManager()
    avd_manager.duplicate_avd(avd_name)

    cmd = ["emulator", "-avd", avd_name, "-no-snapshot"]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
