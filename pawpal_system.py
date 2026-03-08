from __future__ import annotations
from dataclasses import dataclass, field
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

    def mark_complete(self) -> None:
        """Mark this task as done for the current day."""
        self.completed = True

    def reset(self) -> None:
        """Clear completion status (e.g. at the start of a new day)."""
        self.completed = False

    def __str__(self) -> str:
        """Return a one-line human-readable summary of the task."""
        status = "✓" if self.completed else "○"
        return (
            f"[{status}] {self.title} | {self.duration_minutes} min | "
            f"{self.priority.name} | {self.frequency.value}"
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

    def mark_task_complete(self, pet_name: str, task_title: str) -> bool:
        """Find a task by pet + title and mark it complete. Returns True if found."""
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return False
        for task in pet.tasks:
            if task.title.lower() == task_title.lower():
                task.mark_complete()
                return True
        return False

    def summary(self) -> str:
        """Return a one-line status string showing available time and pending workload."""
        pending_count = len(self.owner.all_pending_tasks())
        pending_min = self.owner.total_pending_minutes()
        return (
            f"Owner: {self.owner.name} | "
            f"Available: {self.owner.available_minutes} min | "
            f"Pending tasks: {pending_count} ({pending_min} min total)"
        )
