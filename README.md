# AITK

Android Interactive Toolkit for Emulators. The package is designed to let the MLLM-based agents interact with the Android emulator, perform tasks, and save comprehensive trajectory data. The tasks can be easily customized by the users.

## Installation

Follow the instructions in [docs/setup.md](docs/setup.md) to install the emulator and set up the environment.

## Usage

### Default Tasks (A3)

1. Prepare your agent model following the instructions in [docs/translator.md](docs/translator.md).
2. Modify the `configs/controller.yaml` to set the model type, the API key, and etc.
3. Run the following command to start the task execution:

```bash
python scripts/interact.py
```

### Customize Tasks

Follow the instructions in [docs/task.md](docs/task.md) to customize the tasks.

## ToDo

- [ ] Add parallel execution of tasks.
