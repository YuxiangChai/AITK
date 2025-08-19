import atexit
import signal
import subprocess
import sys

from aitk.utils.avd_manager import AVDManager

if __name__ == "__main__":
    avd_name = "A3V2_dup"
    avd_manager = AVDManager()
    avd_manager.duplicate_avd(avd_name)

    def cleanup(*_args):
        try:
            avd_manager.delete_avd(avd_name)
        except Exception:
            pass

    # Ensure cleanup on normal exit and on Ctrl+C/termination
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, lambda *args: (cleanup(), sys.exit(130)))
    signal.signal(signal.SIGTERM, lambda *args: (cleanup(), sys.exit(143)))

    cmd = ["emulator", "-avd", avd_name, "-no-snapshot"]
    subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)

    # Keep the script alive to catch signals while emulator runs detached
    signal.pause()
