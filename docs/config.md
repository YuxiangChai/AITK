# Config

The default config file is at `configs/controller.yaml`. You can modify it to set up the experiment.

The config file has the following keys:

```yaml
device:
  udid: # The udid of the emulator to use. You can find the udid in the `adb devices` command. "emulator-5554" is the default udid for Android Virtual Device.
  appium_port: # Optional. The port of the Appium server. If not provided, the default port 4723 will be used.

translator: # The translator of the agent to use for the task execution. It should be the file name of the translator file in the aitk/translators directory.
translator_args: # The arguments for the translator if needed.

experiment:
  name: # The name of the experiment, which can be overwritten by the command line argument `--experiment-name`.
  save_root_dir: # The root directory to save the experiment results, in which experiments folders will be saved.
  tasks: # The path to the task jsonl file.
  backend: # The backend to use for the task execution. choose from "adb" or "appium".
  screen_record: # Whether to screen record the process of the task execution. Only support Appium as backend. ADB doesn't support this feature.
  record_resolution: # A list of two integers, the resolution of the screen recording in pixels if screen_record is on.
  resume_exp: # The path of the experiment folder to resume from. If not provided, a new experiment will be started. Default to null.
```
