# task_manager.py
# Purpose: Manage users, tasks, and reports
# Intentional error: in __main__, we call start_app(), but the defined function is named run_app()

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

class User:
    def __init__(self, user_id: int, name: str, email: str):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.created_at = datetime.utcnow()

    def __repr__(self):
        return f"User(id={self.user_id}, name={self.name})"

class Task:
    def __init__(self, task_id: int, title: str, description: str, priority: str, owner: User):
        self.task_id = task_id
        self.title = title
        self.description = description
        self.priority = priority
        self.owner = owner
        self.status = "pending"
        self.created_at = datetime.utcnow()
        self.due_date: Optional[datetime] = None

    def set_due_date(self, days_from_now: int):
        self.due_date = datetime.utcnow() + timedelta(days=days_from_now)

    def mark_done(self):
        self.status = "done"

    def __repr__(self):
        return f"Task(id={self.task_id}, title={self.title}, owner={self.owner.name}, status={self.status})"

class TaskManager:
    def __init__(self):
        self.users: Dict[int, User] = {}
        self.tasks: Dict[int, Task] = {}
        self._next_user_id = 1
        self._next_task_id = 1

    def add_user(self, name: str, email: str) -> User:
        user = User(self._next_user_id, name, email)
        self.users[self._next_user_id] = user
        self._next_user_id += 1
        logger.info(f"Added user {user}")
        return user

    def add_task(self, title: str, description: str, priority: str, owner_id: int) -> Task:
        if owner_id not in self.users:
            raise ValueError("Invalid owner_id")
        task = Task(self._next_task_id, title, description, priority, self.users[owner_id])
        self.tasks[self._next_task_id] = task
        self._next_task_id += 1
        logger.info(f"Added task {task}")
        return task

    def assign_due_dates(self):
        for task in self.tasks.values():
            if task.due_date is None:
                days = random.randint(1, 30)
                task.set_due_date(days)

    def list_tasks(self, status: Optional[str] = None) -> List[Task]:
        if status:
            return [t for t in self.tasks.values() if t.status == status]
        return list(self.tasks.values())

    def mark_task_done(self, task_id: int):
        if task_id not in self.tasks:
            raise ValueError("Task does not exist")
        self.tasks[task_id].mark_done()
        logger.info(f"Task {task_id} marked as done")

    def report(self) -> Dict[str, Any]:
        total = len(self.tasks)
        done = sum(1 for t in self.tasks.values() if t.status == "done")
        pending = total - done
        return {"total": total, "done": done, "pending": pending}

    def save_to_file(self, path: str):
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

    def load_from_file(self, path: str):
        if not os.path.exists(path):
            logger.warning("No saved state found")
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.users = {
            int(uid): User(int(uid), u["name"], u["email"])
            for uid, u in data["users"].items()
        }
        self.tasks = {}
        for tid, t in data["tasks"].items():
            task = Task(
                int(tid), t["title"], t["description"], t["priority"], self.users[t["owner_id"]]
            )
            task.status = t["status"]
            if t["due_date"]:
                task.due_date = datetime.fromisoformat(t["due_date"])
            self.tasks[int(tid)] = task
        logger.info("Loaded state from file")

# Utility functions
def sample_data(manager: TaskManager):
    alice = manager.add_user("Alice", "alice@example.com")
    bob = manager.add_user("Bob", "bob@example.com")

    t1 = manager.add_task("Finish report", "Complete Q1 financial report", "high", alice.user_id)
    t1.set_due_date(7)

    t2 = manager.add_task("Plan event", "Prepare slides for team meeting", "medium", bob.user_id)
    t2.set_due_date(3)

    t3 = manager.add_task("Fix bug", "Resolve login issue", "high", alice.user_id)
    t3.set_due_date(2)

    manager.mark_task_done(t2.task_id)

def run_app():
    manager = TaskManager()
    sample_data(manager)
    manager.assign_due_dates()
    print("Tasks:")
    for t in manager.list_tasks():
        print(f" - {t.title} ({t.status}), due {t.due_date.date() if t.due_date else 'N/A'}")

    print("\nReport:", manager.report())
    manager.save_to_file("tasks.json")
    return manager

#############################################
# Self-tests
#############################################
def _test_users_and_tasks():
    m = TaskManager()
    u = m.add_user("Test", "test@example.com")
    t = m.add_task("Do something", "Test desc", "low", u.user_id)
    assert t.owner.user_id == u.user_id
    print("User and Task creation OK")



if __name__ == "__main__":
    # Run the application using the defined entrypoint
    run_app()
