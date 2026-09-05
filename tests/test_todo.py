import json

import pytest

from todo import TodoList, main


@pytest.fixture
def store_path(tmp_path):
    return tmp_path / "store.json"


def test_add_creates_task(store_path):
    todo = TodoList(store_path=store_path)
    task = todo.add("Buy milk")

    assert task["id"] == 1
    assert task["text"] == "Buy milk"
    assert task["done"] is False
    assert store_path.exists()


def test_ids_increment_and_survive_reload(store_path):
    todo = TodoList(store_path=store_path)
    todo.add("First")
    todo.add("Second")

    reloaded = TodoList(store_path=store_path)
    assert [t["text"] for t in reloaded.tasks] == ["First", "Second"]
    third = reloaded.add("Third")
    assert third["id"] == 3


def test_complete_marks_task_done(store_path):
    todo = TodoList(store_path=store_path)
    todo.add("Task A")

    assert todo.complete(1) is True
    assert todo.tasks[0]["done"] is True
    assert todo.complete(999) is False


def test_remove_deletes_task(store_path):
    todo = TodoList(store_path=store_path)
    todo.add("Task A")
    todo.add("Task B")

    assert todo.remove(1) is True
    assert [t["id"] for t in todo.tasks] == [2]
    assert todo.remove(1) is False


def test_list_filters_pending(store_path):
    todo = TodoList(store_path=store_path)
    todo.add("Task A")
    todo.add("Task B")
    todo.complete(1)

    all_tasks = todo.list(show_all=True)
    pending = todo.list(show_all=False)

    assert len(all_tasks) == 2
    assert len(pending) == 1
    assert pending[0]["text"] == "Task B"


def test_store_persists_valid_json(store_path):
    todo = TodoList(store_path=store_path)
    todo.add("Task A")

    with open(store_path, encoding="utf-8") as f:
        data = json.load(f)
    assert data == [{"id": 1, "text": "Task A", "done": False, "due": None}]


def test_add_with_due_date(store_path):
    todo = TodoList(store_path=store_path)
    task = todo.add("Task A", due="2026-01-01")

    assert task["due"] == "2026-01-01"


def test_format_task_shows_due_date():
    from todo import format_task

    with_due = {"id": 1, "text": "Task A", "done": False, "due": "2026-01-01"}
    without_due = {"id": 2, "text": "Task B", "done": False, "due": None}

    assert format_task(with_due) == "[ ] 1: Task A (due 2026-01-01)"
    assert format_task(without_due) == "[ ] 2: Task B"


def test_cli_add_with_invalid_due_date_errors(store_path, capsys):
    with pytest.raises(SystemExit):
        main(["--store", str(store_path), "add", "Buy milk", "--due", "not-a-date"])
    assert "invalid date" in capsys.readouterr().err


def test_cli_add_and_list(store_path, capsys):
    exit_code = main(["--store", str(store_path), "add", "Buy milk"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Added task 1: Buy milk" in out

    exit_code = main(["--store", str(store_path), "list"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "[ ] 1: Buy milk" in out


def test_cli_done_and_remove(store_path, capsys):
    main(["--store", str(store_path), "add", "Buy milk"])
    capsys.readouterr()

    exit_code = main(["--store", str(store_path), "done", "1"])
    assert exit_code == 0
    assert "Marked task 1 as done." in capsys.readouterr().out

    exit_code = main(["--store", str(store_path), "remove", "1"])
    assert exit_code == 0
    assert "Removed task 1." in capsys.readouterr().out


def test_cli_unknown_id_errors(store_path, capsys):
    exit_code = main(["--store", str(store_path), "done", "42"])
    assert exit_code == 1
    assert "No task with id 42." in capsys.readouterr().err
