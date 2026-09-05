#!/usr/bin/env python3
"""A simple command-line to-do list app."""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

DEFAULT_STORE = Path.home() / ".todo_app.json"


class TodoList:
    def __init__(self, store_path=DEFAULT_STORE):
        self.store_path = Path(store_path)
        self.tasks = self._load()

    def _load(self):
        if not self.store_path.exists():
            return []
        with open(self.store_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self):
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, indent=2)

    def _next_id(self):
        return max((t["id"] for t in self.tasks), default=0) + 1

    def add(self, text, due=None):
        task = {"id": self._next_id(), "text": text, "done": False, "due": due}
        self.tasks.append(task)
        self._save()
        return task

    def remove(self, task_id):
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        self._save()
        return len(self.tasks) < before

    def complete(self, task_id):
        for t in self.tasks:
            if t["id"] == task_id:
                t["done"] = True
                self._save()
                return True
        return False

    def list(self, show_all=True):
        if show_all:
            return list(self.tasks)
        return [t for t in self.tasks if not t["done"]]


def format_task(task):
    box = "x" if task["done"] else " "
    due = task.get("due")
    suffix = f" (due {due})" if due else ""
    return f"[{box}] {task['id']}: {task['text']}{suffix}"


def parse_due(value):
    try:
        date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid date '{value}', expected YYYY-MM-DD")
    return value


def build_parser():
    parser = argparse.ArgumentParser(prog="todo", description="A simple to-do list")
    parser.add_argument("--store", default=str(DEFAULT_STORE), help="Path to the JSON store file")

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_p = subparsers.add_parser("add", help="Add a new task")
    add_p.add_argument("text", help="Task description")
    add_p.add_argument("--due", type=parse_due, help="Due date (YYYY-MM-DD)")

    list_p = subparsers.add_parser("list", help="List tasks")
    list_p.add_argument("--all", action="store_true", help="Include completed tasks (default)")
    list_p.add_argument("--pending", action="store_true", help="Only show pending tasks")

    done_p = subparsers.add_parser("done", help="Mark a task as complete")
    done_p.add_argument("id", type=int, help="Task id")

    remove_p = subparsers.add_parser("remove", help="Remove a task")
    remove_p.add_argument("id", type=int, help="Task id")

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    todo = TodoList(store_path=args.store)

    if args.command == "add":
        task = todo.add(args.text, due=args.due)
        print(f"Added task {task['id']}: {task['text']}")
        return 0

    if args.command == "list":
        tasks = todo.list(show_all=not args.pending)
        if not tasks:
            print("No tasks.")
        for t in tasks:
            print(format_task(t))
        return 0

    if args.command == "done":
        if todo.complete(args.id):
            print(f"Marked task {args.id} as done.")
            return 0
        print(f"No task with id {args.id}.", file=sys.stderr)
        return 1

    if args.command == "remove":
        if todo.remove(args.id):
            print(f"Removed task {args.id}.")
            return 0
        print(f"No task with id {args.id}.", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
