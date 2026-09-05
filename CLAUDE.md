# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Run tests:
```
pytest
```

Run a single test:
```
pytest tests/test_todo.py::test_complete_marks_task_done
```

Run the app:
```
python todo.py add "Buy milk"
python todo.py list
python todo.py done 1
python todo.py remove 1
```

There is no build/lint step configured.

## Architecture

Single-file CLI app (`todo.py`) with two layers:

- `TodoList` — in-memory task list backed by a JSON file. Loads on `__init__`, saves to disk after every mutation (`add`, `remove`, `complete`). Task IDs are assigned as `max(existing ids) + 1`, so IDs are not reused after removal.
- `main()` / `build_parser()` — argparse CLI wrapper around `TodoList`. Each subcommand (`add`, `list`, `done`, `remove`) maps directly to one `TodoList` method and prints a result or an error to stderr with exit code 1.

Default storage path is `~/.todo_app.json`, overridable via the global `--store` flag (this is how tests isolate state via `tmp_path`, and how the CLI arg is threaded through `main(argv)`).

`conftest.py` adds the repo root to `sys.path` so `tests/test_todo.py` can `from todo import TodoList, main` without packaging.
