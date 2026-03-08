from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class Pet:
    name: str
    species: str  # e.g. "dog", "cat", "other"


@dataclass
class Owner:
    name: str
    available_minutes: int
    pet: Pet


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority


@dataclass
class DailyPlan:
    scheduled_tasks: list[Task] = field(default_factory=list)
    explanations: list[str] = field(default_factory=list)

    def display(self) -> str:
        if not self.scheduled_tasks:
            return "No tasks scheduled."
        lines = ["=== Daily Plan ==="]
        for task, reason in zip(self.scheduled_tasks, self.explanations):
            lines.append(f"  • {task.title} ({task.duration_minutes} min) — {reason}")
        return "\n".join(lines)


@dataclass
class Scheduler:
    owner: Owner
    tasks: list[Task] = field(default_factory=list)

    def build_plan(self) -> DailyPlan:
        """
        Select and order tasks that fit within the owner's available time.
        Tasks are sorted by priority (HIGH first), then by duration (shortest first)
        as a tiebreaker so more tasks fit within the time budget.
        """
        plan = DailyPlan()
        time_remaining = self.owner.available_minutes

        sorted_tasks = sorted(
            self.tasks,
            key=lambda t: (-t.priority.value, t.duration_minutes),
        )

        for task in sorted_tasks:
            if task.duration_minutes <= time_remaining:
                plan.scheduled_tasks.append(task)
                plan.explanations.append(
                    f"Priority: {task.priority.name.lower()} — fits in remaining time ({time_remaining} min left)"
                )
                time_remaining -= task.duration_minutes
            else:
                plan.explanations.append(
                    f"Skipped '{task.title}': needs {task.duration_minutes} min, only {time_remaining} min left"
                )

        return plan
