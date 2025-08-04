# Task Specification (Customize Task)

## Task File

For each task, you should create a python file in the `aitk/tasks` directory.

The file should contain a function `task` that returns a dictionary of the task specification and an optional function `eval` that evaluates the task.

The `task` function should return a dictionary containing the following keys:

- `task` (str): the task description
- `app` (str): the app name
- `app_package` (str): the app package string (e.g. `com.rammigsoftware.bluecoins`)
- `max_steps` (int): the maximum number of steps the agent can take
- `level` (str): the level of the task (optional, for evaluation purpose)
- `category` (str): the category of the task (optional, for evaluation purpose)
- `essential_states` (list[str]): the essential states of the task (optional, for essential state evaluation purpose)

If the `eval` function is provided, it should take the following arguments and return a boolean value:

- `task` (str): the task description
- `history` (dict): the history of the task execution
- `answer` (str): the answer of the task (optional)
- `client` (OpenAI): the client of the OpenAI API (optional)
- `model_type` (str): the type of the model (optional)
