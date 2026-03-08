from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Frequency(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    AS_NEEDED = "as_needed"


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet-care activity."""
    title: str
    duration_minutes: int
    priority: Priority
    frequency: Frequency = Frequency.DAILY
    completed: bool = False
    time_of_day: str = "anytime"       # "HH:MM" (e.g. "07:30") or "anytime"
    due_date: date = field(default_factory=date.today)

    def mark_complete(self) -> None:
        """Mark this task as done for the current day."""
        self.completed = True

    def reset(self) -> None:
        """Clear completion status (e.g. at the start of a new day)."""
        self.completed = False

    def next_occurrence(self) -> Task | None:
        """Return a fresh incomplete copy due tomorrow (DAILY), next week (WEEKLY), or None (AS_NEEDED)."""
        if self.frequency == Frequency.DAILY:
            next_due = self.due_date + timedelta(days=1)
        elif self.frequency == Frequency.WEEKLY:
            next_due = self.due_date + timedelta(weeks=1)
        else:
            return None  # AS_NEEDED tasks don't recur automatically

        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            time_of_day=self.time_of_day,
            due_date=next_due,
        )

    def __str__(self) -> str:
        """Return a one-line human-readable summary of the task."""
        status = "✓" if self.completed else "○"
        time_label = f"@{self.time_of_day}" if self.time_of_day != "anytime" else "anytime"
        return (
            f"[{status}] {self.title} | {self.duration_minutes} min | "
            f"{self.priority.name} | {time_label} | due {self.due_date}"
        )


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """A pet with its own list of care tasks."""
    name: str
    species: str          # e.g. "dog", "cat", "other"
    tasks: list[Task] = field(default_factory=list)

    # -- task management ---------------------------------------------------

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> bool:
        """Remove the first task whose title matches. Returns True if found."""
        for i, t in enumerate(self.tasks):
            if t.title.lower() == title.lower():
                self.tasks.pop(i)
                return True
        return False

    def get_pending_tasks(self) -> list[Task]:
        """Return tasks not yet completed."""
        return [t for t in self.tasks if not t.completed]

    def get_completed_tasks(self) -> list[Task]:
        """Return tasks that have already been marked complete."""
        return [t for t in self.tasks if t.completed]

    def reset_daily_tasks(self) -> None:
        """Reset all DAILY tasks at the start of a new day."""
        for task in self.tasks:
            if task.frequency == Frequency.DAILY:
                task.reset()

    def total_task_minutes(self) -> int:
        """Return the combined duration of all tasks for this pet."""
        return sum(t.duration_minutes for t in self.tasks)

    def __str__(self) -> str:
        """Return a one-line summary of the pet and their task count."""
        return f"{self.name} ({self.species}) — {len(self.tasks)} task(s)"


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    """A pet owner who may have one or more pets."""
    name: str
    available_minutes: int
    pets: list[Pet] = field(default_factory=list)

    # -- pet management ----------------------------------------------------

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's list of pets."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> bool:
        """Remove the first pet whose name matches. Returns True if found."""
        for i, p in enumerate(self.pets):
            if p.name.lower() == name.lower():
                self.pets.pop(i)
                return True
        return False

    def get_pet(self, name: str) -> Pet | None:
        """Return the pet with the given name, or None if not found."""
        for p in self.pets:
            if p.name.lower() == name.lower():
                return p
        return None

    # -- cross-pet task access ---------------------------------------------

    def all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every (pet, task) pair across all pets."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def all_pending_tasks(self) -> list[tuple[Pet, Task]]:
        """Return all incomplete (pet, task) pairs across every pet."""
        return [(pet, task) for pet in self.pets for task in pet.get_pending_tasks()]

    def total_pending_minutes(self) -> int:
        """Return total time needed for all pending tasks across all pets."""
        return sum(task.duration_minutes for _, task in self.all_pending_tasks())

    def __str__(self) -> str:
        """Return a one-line summary of the owner and their pets."""
        return (
            f"{self.name} | {self.available_minutes} min available | "
            f"{len(self.pets)} pet(s)"
        )

    # -- persistence -------------------------------------------------------

    def save_to_json(self, filepath: str = "pawpal_data.json") -> None:
        """Serialise the owner, all pets, and all tasks to a JSON file."""
        data = {
            "name": self.name,
            "available_minutes": self.available_minutes,
            "pets": [
                {
                    "name": pet.name,
                    "species": pet.species,
                    "tasks": [
                        {
                            "title": task.title,
                            "duration_minutes": task.duration_minutes,
                            "priority": task.priority.name,
                            "frequency": task.frequency.value,
                            "completed": task.completed,
                            "time_of_day": task.time_of_day,
                            "due_date": task.due_date.isoformat(),
                        }
                        for task in pet.tasks
                    ],
                }
                for pet in self.pets
            ],
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_json(cls, filepath: str = "pawpal_data.json") -> Owner:
        """Reconstruct an Owner (with all pets and tasks) from a file saved by save_to_json."""
        with open(filepath) as f:
            data = json.load(f)
        owner = cls(name=data["name"], available_minutes=data["available_minutes"])
        for pet_data in data.get("pets", []):
            pet = Pet(name=pet_data["name"], species=pet_data["species"])
            for td in pet_data.get("tasks", []):
                task = Task(
                    title=td["title"],
                    duration_minutes=td["duration_minutes"],
                    priority=Priority[td["priority"]],
                    frequency=Frequency(td["frequency"]),
                    completed=td["completed"],
                    time_of_day=td["time_of_day"],
                    due_date=date.fromisoformat(td["due_date"]),
                )
                pet.add_task(task)
            owner.add_pet(pet)
        return owner


# ---------------------------------------------------------------------------
# DailyPlan
# ---------------------------------------------------------------------------

@dataclass
class DailyPlan:
    """Result of a scheduling run: ordered tasks with per-task explanations."""
    scheduled: list[tuple[Pet, Task]] = field(default_factory=list)
    skipped: list[tuple[Pet, Task, str]] = field(default_factory=list)  # (pet, task, reason)

    def display(self) -> str:
        """Format the plan as a printable string with scheduled and skipped tasks."""
        lines = ["=== Daily Plan ==="]
        if self.scheduled:
            cumulative = 0
            for pet, task in self.scheduled:
                cumulative += task.duration_minutes
                lines.append(
                    f"  ✓ [{pet.name}] {task.title} — "
                    f"{task.duration_minutes} min  (running total: {cumulative} min)"
                )
        else:
            lines.append("  (no tasks fit within available time)")

        if self.skipped:
            lines.append("\n--- Skipped ---")
            for pet, task, reason in self.skipped:
                lines.append(f"  ✗ [{pet.name}] {task.title} — {reason}")

        return "\n".join(lines)

    def total_minutes(self) -> int:
        """Return the total time consumed by all scheduled tasks."""
        return sum(task.duration_minutes for _, task in self.scheduled)


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Retrieves, organises, and schedules tasks across all of an owner's pets.

    Scheduling rules
    ----------------
    1. Only pending (not yet completed) tasks are considered.
    2. Tasks are sorted HIGH → LOW priority; shortest duration breaks ties so
       more tasks can fit within the time budget.
    3. Tasks are greedily selected until available_minutes is exhausted.
    """

    def __init__(self, owner: Owner) -> None:
        """Initialise the scheduler with the owner whose pets will be planned."""
        self.owner = owner

    # -- task retrieval helpers --------------------------------------------

    def pending_tasks_by_priority(self) -> list[tuple[Pet, Task]]:
        """All pending tasks across all pets, sorted by scheduling rules."""
        pairs = self.owner.all_pending_tasks()
        return sorted(pairs, key=lambda pt: (-pt[1].priority.value, pt[1].duration_minutes))

    def tasks_for_pet(self, pet_name: str) -> list[Task]:
        """Return all tasks (pending and complete) for a named pet."""
        pet = self.owner.get_pet(pet_name)
        return pet.tasks if pet else []

    def high_priority_tasks(self) -> list[tuple[Pet, Task]]:
        """Return all pending HIGH-priority (pet, task) pairs across all pets."""
        return [(p, t) for p, t in self.owner.all_pending_tasks() if t.priority == Priority.HIGH]

    # -- plan building -----------------------------------------------------

    def build_plan(self) -> DailyPlan:
        """Greedily schedule all pending tasks across pets within the owner's time budget."""
        plan = DailyPlan()
        time_remaining = self.owner.available_minutes

        for pet, task in self.pending_tasks_by_priority():
            if task.duration_minutes <= time_remaining:
                plan.scheduled.append((pet, task))
                time_remaining -= task.duration_minutes
            else:
                reason = (
                    f"needs {task.duration_minutes} min, "
                    f"only {time_remaining} min left"
                )
                plan.skipped.append((pet, task, reason))

        return plan

    def build_plan_for_pet(self, pet_name: str) -> DailyPlan:
        """Build a plan scoped to a single pet."""
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return DailyPlan()

        plan = DailyPlan()
        time_remaining = self.owner.available_minutes
        sorted_tasks = sorted(
            pet.get_pending_tasks(),
            key=lambda t: (-t.priority.value, t.duration_minutes),
        )

        for task in sorted_tasks:
            if task.duration_minutes <= time_remaining:
                plan.scheduled.append((pet, task))
                time_remaining -= task.duration_minutes
            else:
                reason = (
                    f"needs {task.duration_minutes} min, "
                    f"only {time_remaining} min left"
                )
                plan.skipped.append((pet, task, reason))

        return plan

    def mark_task_complete(self, pet_name: str, task_title: str) -> Task | None:
        """
        Mark a task complete and, for DAILY/WEEKLY tasks, append the next
        occurrence to the pet's task list automatically.

        Returns the newly created next-occurrence Task, or None if the task
        was AS_NEEDED (no recurrence) or not found.
        """
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return None
        for task in pet.tasks:
            if task.title.lower() == task_title.lower() and not task.completed:
                task.mark_complete()
                next_task = task.next_occurrence()  # None for AS_NEEDED
                if next_task is not None:
                    pet.add_task(next_task)
                return next_task
        return None

    def sort_by_time(self) -> list[tuple[Pet, Task]]:
        """Return all tasks sorted chronologically by time_of_day; 'anytime' tasks sort last."""
        return sorted(
            self.owner.all_tasks(),
            key=lambda pt: (pt[1].time_of_day == "anytime", pt[1].time_of_day),
        )

    def tasks_sorted_by_duration(self, ascending: bool = True) -> list[tuple[Pet, Task]]:
        """Return all pending tasks sorted by duration (shortest or longest first)."""
        pairs = self.owner.all_pending_tasks()
        return sorted(pairs, key=lambda pt: pt[1].duration_minutes, reverse=not ascending)

    def filter_by_pet(self, pet_name: str) -> list[Task]:
        """Return all tasks (any status) belonging to the named pet."""
        pet = self.owner.get_pet(pet_name)
        return pet.tasks if pet else []

    def filter_by_status(self, completed: bool) -> list[tuple[Pet, Task]]:
        """Return (pet, task) pairs filtered by completion status."""
        return [
            (pet, task)
            for pet, task in self.owner.all_tasks()
            if task.completed == completed
        ]

    def due_today(self) -> list[tuple[Pet, Task]]:
        """Return pending tasks whose frequency makes them due every day."""
        return [
            (pet, task)
            for pet, task in self.owner.all_pending_tasks()
            if task.frequency == Frequency.DAILY
        ]

    def detect_conflicts(self) -> list[str]:
        """Return warning strings for time overload, impossible tasks, duplicate titles, and time-slot clashes."""
        conflicts: list[str] = []
        available = self.owner.available_minutes

        total_pending = self.owner.total_pending_minutes()
        if total_pending > available:
            conflicts.append(
                f"Time overload: {total_pending} min of tasks but only "
                f"{available} min available — "
                f"{total_pending - available} min will be skipped."
            )

        for pet, task in self.owner.all_pending_tasks():
            if task.duration_minutes > available:
                conflicts.append(
                    f"Impossible task: [{pet.name}] '{task.title}' needs "
                    f"{task.duration_minutes} min but the entire day is only {available} min."
                )

        for pet in self.owner.pets:
            seen: set[str] = set()
            for task in pet.tasks:
                key = task.title.lower()
                if key in seen:
                    conflicts.append(
                        f"Duplicate task on {pet.name}: '{task.title}' appears more than once."
                    )
                seen.add(key)

        # Time clash detection — group all pending timed tasks by time_of_day,
        # then warn for any slot that has more than one task.
        # Uses a dict[time_slot -> list[(pet_name, task_title)]] so the warning
        # message can name exactly which tasks collide without raising an error.
        time_slots: dict[str, list[tuple[str, str]]] = {}
        for pet, task in self.owner.all_pending_tasks():
            if task.time_of_day == "anytime":
                continue  # unscheduled tasks can't clash
            slot = task.time_of_day
            time_slots.setdefault(slot, []).append((pet.name, task.title))

        for slot, entries in time_slots.items():
            if len(entries) > 1:
                names = ", ".join(f"[{p}] {t}" for p, t in entries)
                conflicts.append(
                    f"Time clash at {slot}: {len(entries)} tasks overlap — {names}"
                )

        return conflicts

    def summary(self) -> str:
        """Return a one-line status string showing available time and pending workload."""
        pending_count = len(self.owner.all_pending_tasks())
        pending_min = self.owner.total_pending_minutes()
        return (
            f"Owner: {self.owner.name} | "
            f"Available: {self.owner.available_minutes} min | "
            f"Pending tasks: {pending_count} ({pending_min} min total)"
        )
