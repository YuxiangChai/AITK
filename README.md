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

### Step 1. Prepare the agent

Follow the instructions in [docs/translator.md](docs/translator.md) to prepare your agent model. Qwen2.5-VL is already supported as an example in `aitk/translators/qwen25_vl.py`.

### Step 2. Modify the config file

Modify the config file in `config/config.yaml` to set up the experiment. More details can be found in [docs/config.md](docs/config.md).

### Step 3. Simple test (ADB method)

Then you can run the following command to start the interaction.

For Linux/Mac:

```shell
bash scripts/single_run.sh
```

For Windows:

```shell
.\scripts\win_single_run.ps1
```

<details>
<summary><h3>Step 3. Advanced Usage (Step 2 breakdown and more features)</h2></summary>

#### 1. Start the AVD (duplicated AVD)

After the AVD is set up and Google account and Pinterest account are logged in and the AVD is shut down, use the following command to start a new AVD for task execution:

```bash
python scripts/start_avd.py
```

This will duplicate the initial AVD and all the tasks will be executed on the duplicated AVD, so that each time you test your agent, the same environment will be used.

#### 2. Run the Agent

If you only use ADB, you can skip this step. If you want to use Appium, after the emulator finishes the boosting, first start Appium service in one terminal:

```bash
appium
```

Then run the following command in another terminal to start testing and interaction.

```bash
python scripts/interact.py
```

You can use `--config` to overwrite the config file path and `--experiment-name` to overwrite the experiment name.

#### 3. Multiple tests (For data collection)

For Linux/Mac:

```bash
bash scripts/multi_run.sh
```

For Windows:

```shell
.\scripts\win_multi_run.ps1
```

## Task Customization

You can follow the instructions in [docs/task.md](docs/task.md) to customize the tasks.

## ToDo

- [ ] Add parallel execution of tasks.
