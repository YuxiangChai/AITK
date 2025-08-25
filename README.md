# AITK

Android Interactive Toolkit for Emulators. This repository is originally developed for the paper [A3](https://arxiv.org/abs/2501.01149). It is lightweight and designed to let any MLLM-based agent or human annotator interact with the Android emulator (AVD), perform tasks, and save comprehensive trajectory data. It can be used to test agents and collect trajectory data. Since it is extremely flexible and extensible, we decided to release it as a data collection and testing tool for the community. We provide an AVD image for A3 evaluation, however, you can also use this repo to create your own AVD image and test your agents.

To evaluate the performance of the agent (such as [A3](https://arxiv.org/abs/2501.01149)), we provide another package [M-Evaluator](https://github.com/YuxiangChai/M-Evaluator), which is a comprehensive and easy-use MLLM-based evaluation system. It includes several MLLM-based evaluation methods (MLLM-as-a-judge) and is designed to be used with any data format.

## Contents

- [Installation & Setup](#installation--setup)
- [Usage](#usage)
  - [Step 1. Prepare the agent](#step-1-prepare-the-agent)
  - [Step 2. Modify the config file](#step-2-modify-the-config-file)
  - [Step 3. Simple test (ADB method)](#step-3-simple-test-adb-method)
  - [Advanced Usage (detailed features)](#advanced-usage-detailed-features)
  - [Human Annotation](#human-annotation)
- [Customize AVD](#customize-avd)
- [Task Customization](#task-customization)
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

```shell
python scripts/interact.py --config <config-file> --experiment-name <experiment-name>
```

You can also use `--resume-exp <experiment-path>` to resume the existing experiment.

<details>
<summary><h3>Advanced Usage (detailed features)</h3></summary>

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

Then run the following command in another terminal to start testing and interaction. Since AVD is not stable and may crash during the interaction, we implement a mechanism to automatically duplicate the AVD when it crashes.

```bash
python scripts/interact.py
```

You can use `--config` to overwrite the config file path and `--experiment-name` to overwrite the experiment name and `--resume-exp` to resume the existing experiment.

#### 3. Multiple tests (For data collection)

For Linux/Mac:

```bash
bash scripts/multi_run.sh
```

For Windows:

```shell
.\scripts\win_multi_run.ps1
```

</details>

### Human Annotation

You can also use this repo to collect human annotations. Run the following command to start the human annotation.

```shell
python scripts/m_annotator.py -j <task-json-file>
```

## Customize AVD

- create a new AVD through Android Studio
- run the following command to initialize the AVD, and you can customize the AVD as you wish.
  ```shell
  python scripts/init_avd.py -a <avd-name>
  ```
- after your AVD is setp up, close it and this will be the base AVD. All tests will be executed on a duplicated AVD to keep the base AVD clean.
- run the following command to run a duplicated AVD
  ```shell
  python scripts/start_avd.py -a <avd-name>
  ```
- you can test your agent on the duplicated AVD by running the following command
  ```shell
  python scripts/interact.py -c <config-file> -e <experiment-name>
  ```

## Task Customization

You can follow the instructions in [docs/task.md](docs/task.md) to customize the tasks.

## ToDo

- [ ] Add parallel execution of tasks.
