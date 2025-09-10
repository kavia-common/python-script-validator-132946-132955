# task_manager.py
# Purpose: Manage users, tasks, and reports with basic in-memory storage and simple file persistence.

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# PUBLIC_INTERFACE
class User:
    """Represents a user who can own tasks."""

    def __init__(self, user_id: int, name: str, email: str) -> None:
        """
        Initialize a User.

        Args:
            user_id: Unique identifier for the user.
            name: Full name of the user.
            email: Email address of the user.
        """
        self.user_id = user_id
        self.name = name
        self.email = email
        self.created_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f"User(id={self.user_id}, name={self.name})"


# PUBLIC_INTERFACE
class Task:
    """Represents a task owned by a user with a title, description, and priority."""

    def __init__(self, task_id: int, title: str, description: str, priority: str, owner: User) -> None:
        """
        Initialize a Task.

        Args:
            task_id: Unique identifier for the task.
            title: Title of the task.
            description: Detailed description of the task.
            priority: Priority as 'low', 'medium', or 'high'.
            owner: The User who owns this task.
        """
        self.task_id = task_id
        self.title = title
        self.description = description
        self.priority = priority
        self.owner = owner
        self.status = "pending"
        self.created_at = datetime.utcnow()
        self.due_date: Optional[datetime] = None

    def set_due_date(self, days_from_now: int) -> None:
        """
        Set the due date a number of days from now.

        Args:
            days_from_now: Non-negative number of days from now.

        Raises:
            ValueError: If days_from_now is negative.
        """
        if days_from_now < 0:
            raise ValueError("Due date cannot be negative")
        self.due_date = datetime.utcnow() + timedelta(days=days_from_now)

    def mark_done(self) -> None:
        """Mark the task as done."""
        self.status = "done"

    def __repr__(self) -> str:
        return f"Task(id={self.task_id}, title={self.title}, owner={self.owner.name}, status={self.status})"


# PUBLIC_INTERFACE
class TaskManager:
    """In-memory manager for Users and Tasks, with simple JSON file persistence."""

    def __init__(self) -> None:
        """Initialize the TaskManager with empty stores and id counters."""
        self.users: Dict[int, User] = {}
        self.tasks: Dict[int, Task] = {}
        self._next_user_id = 1
        self._next_task_id = 1

    # PUBLIC_INTERFACE
    def add_user(self, name: str, email: str) -> User:
        """
        Add a new user.

        Args:
            name: User's full name.
            email: User's email address. Must contain '@'.

        Returns:
            The created User.

        Raises:
            ValueError: If the provided email is invalid.
        """
        if "@" not in email:
            raise ValueError("Invalid email format")
        user = User(self._next_user_id, name, email)
        self.users[self._next_user_id] = user
        self._next_user_id += 1
        logger.info(f"Added user {user}")
        return user

    # PUBLIC_INTERFACE
    def add_task(self, title: str, description: str, priority: str, owner_id: int) -> Task:
        """
        Add a new task for a given user.

        Args:
            title: Title of the task.
            description: Detailed description.
            priority: 'low', 'medium', or 'high' (case-insensitive). Defaults to 'low' if invalid.
            owner_id: The user_id of the owner.

        Returns:
            The created Task.

        Raises:
            ValueError: If the owner_id does not exist.
        """
        if owner_id not in self.users:
            raise ValueError("Invalid owner_id")
        if priority.lower() not in ["low", "medium", "high"]:
            logger.warning(f"Unknown priority '{priority}', defaulting to 'low'")
            priority = "low"
        else:
            priority = priority.lower()

        task = Task(self._next_task_id, title, description, priority, self.users[owner_id])
        self.tasks[self._next_task_id] = task
        self._next_task_id += 1
        logger.info(f"Added task {task}")
        return task

    # PUBLIC_INTERFACE
    def assign_due_dates(self) -> None:
        """
        Assign random due dates between 1 and 30 days from now to tasks without due dates.
        """
        for task in self.tasks.values():
            if task.due_date is None:
                days = random.randint(1, 30)
                task.set_due_date(days)

    # PUBLIC_INTERFACE
    def list_tasks(self, status: Optional[str] = None) -> List[Task]:
        """
        List tasks, optionally filtered by status.

        Args:
            status: Optional status to filter by (case-insensitive). Examples: 'pending', 'done'.

        Returns:
            List of Task objects.
        """
        if status:
            return [t for t in self.tasks.values() if t.status.lower() == status.lower()]
        return list(self.tasks.values())

    # PUBLIC_INTERFACE
    def mark_task_done(self, task_id: int) -> None:
        """
        Mark a specific task as done.

        Args:
            task_id: The id of the task to mark as done.

        Raises:
            ValueError: If the task_id does not exist.
        """
        if task_id not in self.tasks:
            raise ValueError("Task does not exist")
        self.tasks[task_id].mark_done()
        logger.info(f"Task {task_id} marked as done")

    # PUBLIC_INTERFACE
    def report(self) -> Dict[str, Any]:
        """
        Generate a summary report of tasks.

        Returns:
            A dictionary with keys 'total', 'done', 'pending'.
        """
        total = len(self.tasks)
        done = sum(1 for t in self.tasks.values() if t.status == "done")
        pending = total - done
        return {"total": total, "done": done, "pending": pending}

    # PUBLIC_INTERFACE
    def save_to_file(self, path: str) -> None:
        """
        Save current users and tasks to a JSON file.

        Args:
            path: File path to write JSON data.
        """
        data = {
            "users": {uid: {"name": u.name, "email": u.email} for uid, u in self.users.items()},
            "tasks": {
                tid: {
                    "title": t.title,
                    "description": t.description,
                    "priority": t.priority,
                    "owner_id": t.owner.user_id,
                    "status": t.status,
                    "due_date": t.due_date.isoformat() if t.due_date else None
                }
                for tid, t in self.tasks.items()
            }
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved state to {path}")

    # PUBLIC_INTERFACE
    def load_from_file(self, path: str) -> None:
        """
        Load users and tasks from a JSON file.

        Args:
            path: File path to read JSON data from.

        Notes:
            - If the file does not exist, nothing is loaded.
            - Invalid due_date strings are logged and ignored for that task.
        """
        if not os.path.exists(path):
            logger.warning("No saved state found")
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.users = {
            int(uid): User(int(uid), u["name"], u["email"])
            for uid, u in data.get("users", {}).items()
        }

        self.tasks = {}
        for tid, t in data.get("tasks", {}).items():
            owner_id = t["owner_id"]
            if owner_id not in self.users:
                logger.error(f"Owner id {owner_id} not found for task {tid}; skipping task.")
                continue
            task = Task(
                int(tid), t["title"], t["description"], t["priority"], self.users[owner_id]
            )
            task.status = t.get("status", "pending")
            if t.get("due_date"):
                try:
                    task.due_date = datetime.fromisoformat(t["due_date"])
                except Exception as e:
                    logger.error(f"Failed to parse due_date for task {tid}: {e}")
            self.tasks[int(tid)] = task
        logger.info("Loaded state from file")


# PUBLIC_INTERFACE
def sample_data(manager: TaskManager) -> None:
    """
    Populate the TaskManager with a small set of sample users and tasks.

    Args:
        manager: The TaskManager instance to populate.
    """
    alice = manager.add_user("Alice", "alice@example.com")
    bob = manager.add_user("Bob", "bob@example.com")

    t1 = manager.add_task("Finish report", "Complete Q1 financial report", "high", alice.user_id)
    t1.set_due_date(7)

    t2 = manager.add_task("Plan event", "Prepare slides for team meeting", "medium", bob.user_id)
    t2.set_due_date(3)

    t3 = manager.add_task("Fix bug", "Resolve login issue", "high", alice.user_id)
    t3.set_due_date(2)

    manager.mark_task_done(t2.task_id)


# PUBLIC_INTERFACE
def run_app() -> TaskManager:
    """
    Entry point to demonstrate TaskManager operations.

    Returns:
        The TaskManager instance after running sample operations.
    """
    manager = TaskManager()
    sample_data(manager)
    manager.assign_due_dates()
    print("Tasks:")
    for t in manager.list_tasks():
        due = t.due_date.date() if t.due_date else 'N/A'
        print(f" - {t.title} ({t.status}), due {due}")

    print("\nReport:", manager.report())
    # Persist to a local JSON file; in production, this can be configured via environment or external storage
    manager.save_to_file("tasks.json")
    return manager


def _test_users_and_tasks() -> None:
    """
    Basic internal test to validate user and task creation and ownership linkage.
    """
    m = TaskManager()
    u = m.add_user("Test", "test@example.com")
    t = m.add_task("Do something", "Test desc", "low", u.user_id)
    assert t.owner.user_id == u.user_id
    print("User and Task creation OK")


def _test_report() -> None:
    """
    Basic internal test to validate the generated report counts.
    """
    m = TaskManager()
    u = m.add_user("X", "x@x.com")
    m.add_task("Task1", "Desc", "low", u.user_id)
    m.add_task("Task2", "Desc", "low", u.user_id)
    m.mark_task_done(1)
    r = m.report()
    assert r["done"] == 1
    assert r["pending"] == 1
    print("Report OK")


if __name__ == "__main__":
    # Run the application using the defined entrypoint
    run_app()
