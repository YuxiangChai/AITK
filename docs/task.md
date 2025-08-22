# Task Customization

We use a `.jsonl` file to store the tasks. Each line is a task, which is a dictionary with the following keys:

- `name` (str): the name of the task. such as "cnn_tariff"
- `task` (str): the task instruction
- `app` (str): the app name. such as "cnn"
- `app_package` (str): the app package string (e.g. `com.cnn.mobile.android.phone`)
- `max_steps` (int): the maximum number of steps the agent can take
- `level` (str): the level of the task (optional, for evaluation purpose)
- `category` (str): the category of the task (optional, for evaluation purpose)
- `essential_states` (list[str]): the essential states of the task (optional, for essential state evaluation purpose)

## New Task

You can follow the style above to create new tasks and save them in a `.jsonl` file.

## New App and Task

You need to use the following command to start the base AVD and install new apps and login (if needed). If you need task pre-requisites (e.g., uploaded files, apps setup, etc.) which need to be initialized everytime you start a new test, you should also operate them in the base AVD.

```shell
python scripts/init_avd.py
```

Close the base AVD and next time you start a new test, a duplicated AVD will be used.
