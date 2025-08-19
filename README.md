# AITK

Android Interactive Toolkit for Emulators. The package is designed to let the MLLM-based agents interact with the Android emulator, perform tasks, and save comprehensive trajectory data. The tasks can be easily customized by the users.

## Contents

- [Installation & Setup](#installation--setup)
- [Usage](#usage)
  - [1. Start the AVD](#1-start-the-avd)
  - [2. Prepare the Agent](#2-prepare-the-agent)
  - [3. Run the Agent](#3-run-the-agent)
- [ToDo](#todo)

## Installation & Setup

Follow the instructions in [docs/setup.md](docs/setup.md) to install the emulator and set up the environment. This may take a while but once it's done, no more modification is needed.

## Usage

### 1. Start the AVD

After the AVD is set up and Google account is logged in and the AVD is shut down, use the following command to start a new AVD for task execution:

```bash
python scripts/start_avd.py
```

This will duplicate the initial AVD and all the tasks will be executed on the duplicated AVD, so that each time you test your agent, a same environment will be used.

### 2. Prepare the Agent

Follow the instructions in [docs/translator.md](docs/translator.md) to prepare your agent model. Qwen2.5-VL is already supported as an example in `aitk/translators/qwen25_vl.py`.

### 3. Run the Agent

ToDo

## ToDo

- [ ] Add parallel execution of tasks.
