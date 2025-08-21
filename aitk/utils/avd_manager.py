import shutil
from pathlib import Path

from aitk import aitk_logger, get_os


class AVDManager:
    def __init__(self) -> None:
        self.avd_root_dir = Path.home() / ".android" / "avd"
        if not self.avd_root_dir.exists():
            aitk_logger.error(f"AVD root directory '{self.avd_root_dir}' not found.")
            exit(1)

        if get_os() == "mac":
            self.sdk_dir = Path.home() / "Library" / "Android" / "sdk"
            self.device_arch = "arm64-v8a"
        elif get_os() == "linux":
            self.sdk_dir = Path.home() / "Android" / "Sdk"
            self.device_arch = "x86_64"
        elif get_os() == "win":
            self.sdk_dir = Path.home() / "AppData" / "Local" / "Android" / "Sdk"
            self.device_arch = "x86_64"
        else:
            aitk_logger.error(f"Unsupported OS: {get_os()}")
            exit(1)

        self.arc_dir = (
            self.sdk_dir
            / "system-images"
            / "android-35"
            / "google_apis_playstore"
            / self.device_arch
        )

    def _remove_lock_files(self, avd_name: str = "A3V2") -> None:
        lock_files = self.avd_root_dir.glob(f"{avd_name}.avd/*.lock")
        for lock_file in lock_files:
            lock_file.unlink()

    def _modify_avd_ini_file(self, avd_name: str = "A3V2") -> None:
        avd_init = self.avd_root_dir / f"{avd_name}.ini"
        new_init_content = f"avd.ini.encoding=UTF-8\npath={self.avd_root_dir / f'{avd_name}.avd'}\npath.rel=avd/{avd_name}.avd\ntarget=android-35"
        with open(avd_init, "w") as f:
            f.write(new_init_content)
        aitk_logger.info(f"AVD init file '{avd_init}' modified.")

    def _modify_avd_config_ini_file(self, avd_name: str = "A3V2") -> None:
        avd_config = self.avd_root_dir / f"{avd_name}.avd" / "config.ini"
        with open(avd_config, "r") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if line.startswith("AvdId="):
                lines[i] = f"AvdId={avd_name}\n"
            elif line.startswith("avd.ini.displayname="):
                lines[i] = f"avd.ini.displayname={avd_name}\n"
            elif line.startswith("abi.type="):
                lines[i] = f"abi.type={self.device_arch}\n"
            elif line.startswith("hw.cpu.arch="):
                if get_os() == "mac":
                    lines[i] = f"hw.cpu.arch=arm64\n"
                else:
                    lines[i] = f"hw.cpu.arch=x86_64\n"
            elif line.startswith("image.sysdir.1="):
                lines[i] = (
                    f"image.sysdir.1={Path('system-images') / 'android-35' / 'google_apis_playstore' / self.device_arch}\n"
                )
            elif line.startswith("skin.path="):
                lines[i] = f"skin.path={self.sdk_dir / 'skins' / 'pixel_7'}\n"

        with open(avd_config, "w") as f:
            f.writelines(lines)
        aitk_logger.info(f"AVD config file '{avd_config}' modified.")

    def _modify_hardware_qemu_ini_file(self, avd_name: str = "A3V2") -> None:
        avd_hardware = self.avd_root_dir / f"{avd_name}.avd" / "hardware-qemu.ini"
        with open(avd_hardware, "r") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if line.startswith("hw.cpu.arch="):
                lines[i] = f"hw.cpu.arch={self.device_arch}\n"
            elif line.startswith("disk.cachePartition.path="):
                lines[i] = (
                    f"disk.cachePartition.path={self.avd_root_dir / '..' / 'avd' / f'{avd_name}.avd' / 'cache.img'}\n"
                )
            elif line.startswith("kernel.path="):
                lines[i] = f"{self.arc_dir / 'kernel-ranchu'}\n"
            elif line.startswith("disk.ramdisk.path="):
                lines[i] = f"{self.arc_dir / 'ramdisk.img'}\n"
            elif line.startswith("disk.systemPartition.initPath="):
                lines[i] = f"{self.arc_dir / 'system.img'}\n"
            elif line.startswith("disk.vendorPartition.initPath="):
                lines[i] = f"{self.arc_dir / 'vendor.img'}\n"
            elif line.startswith("disk.dataPartition.path="):
                lines[i] = (
                    f"{self.avd_root_dir / '..' / 'avd' / f'{avd_name}.avd' / 'userdata-qemu.img'}\n"
                )
            elif line.startswith("disk.encryptionKeyPartition.path="):
                lines[i] = (
                    f"{self.avd_root_dir / '..' / 'avd' / f'{avd_name}.avd' / 'encryptionkey.img'}\n"
                )
            elif line.startswith("android.sdk.root="):
                lines[i] = f"{self.sdk_dir}\n"
            elif line.startswith("android.avd.home="):
                lines[i] = f"{self.avd_root_dir}\n"

        with open(avd_hardware, "w") as f:
            f.writelines(lines)
        aitk_logger.info(f"AVD hardware file '{avd_hardware}' modified.")

    def modify_origin_avd(self) -> None:
        self._remove_lock_files()
        self._modify_avd_ini_file()
        self._modify_avd_config_ini_file()
        self._modify_hardware_qemu_ini_file()

    def duplicate_avd(self, new_avd_name: str = "A3V2_dup") -> None:
        # self._remove_lock_files(new_avd_name)
        shutil.copytree(
            self.avd_root_dir / "A3V2.avd",
            self.avd_root_dir / f"{new_avd_name}.avd",
            dirs_exist_ok=True,
        )
        shutil.copy(
            self.avd_root_dir / "A3V2.ini", self.avd_root_dir / f"{new_avd_name}.ini"
        )
        self._modify_avd_ini_file(new_avd_name)
        self._modify_avd_config_ini_file(new_avd_name)
        self._modify_hardware_qemu_ini_file(new_avd_name)

    def delete_avd(self, avd_name: str = "A3V2_dup") -> None:
        avd_dir = self.avd_root_dir / f"{avd_name}.avd"
        ini_file = self.avd_root_dir / f"{avd_name}.ini"

        if avd_dir.exists():
            shutil.rmtree(avd_dir, ignore_errors=True)
        if ini_file.exists():
            try:
                ini_file.unlink()
            except IsADirectoryError:
                shutil.rmtree(ini_file, ignore_errors=True)
        aitk_logger.info(f"Deleted AVD '{avd_name}'.")
