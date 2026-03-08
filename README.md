# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Smarter Scheduling

Beyond the basic greedy planner, PawPal+ includes several advanced scheduling features:

**Chronological sorting** — Tasks can carry an optional `time_of_day` field in `"HH:MM"` format. `Scheduler.sort_by_time()` orders all tasks from earliest to latest; tasks marked `"anytime"` always sort to the end. Zero-padded `"HH:MM"` strings compare correctly with plain Python string ordering — no `datetime` parsing needed.

**Recurring tasks** — Each `Task` has a `Frequency` (`DAILY`, `WEEKLY`, or `AS_NEEDED`) and a `due_date`. When `Scheduler.mark_task_complete()` is called, `Task.next_occurrence()` automatically creates the next instance using `timedelta` (`+1 day` for daily, `+7 days` for weekly) and appends it to the pet's task list. `AS_NEEDED` tasks return `None` and are not re-queued.

**Conflict detection** — `Scheduler.detect_conflicts()` performs four lightweight checks before scheduling and returns human-readable warning strings instead of raising exceptions:
- **Time overload** — total pending minutes exceed the owner's available time.
- **Impossible task** — a single task is longer than the entire available window.
- **Duplicate titles** — the same task name appears more than once on a pet.
- **Time-slot clash** — two or more tasks share an identical `time_of_day` value.

**Filtering** — `filter_by_pet()` and `filter_by_status()` let the UI (or tests) query tasks by owner, pet name, or completion state without rebuilding the full plan.

## Testing PawPal+

Run the full test suite with:

```bash
python -m pytest
```

### What the tests cover

The 27 tests in `tests/test_pawpal.py` verify the most critical scheduling behaviours across three categories:

- **Task lifecycle** — defaults, `mark_complete()`, `reset()`, and idempotency (marking an already-completed task does nothing).
- **Recurring tasks** — `next_occurrence()` produces a fresh incomplete copy due +1 day (DAILY) or +7 days (WEEKLY); `AS_NEEDED` returns `None`. Completing a recurring task via `Scheduler.mark_task_complete()` automatically enqueues the next occurrence.
- **Pet task management** — `add_task()`, `remove_task()` (returns `True`/`False`), `get_pending_tasks()`, and `reset_daily_tasks()` (clears DAILY only, leaves WEEKLY untouched).
- **Scheduler — happy paths** — greedy planner skips tasks that exceed remaining time, schedules HIGH-priority tasks before LOW, and ignores already-completed tasks.
- **Scheduler — edge cases** — empty owner, pet with no tasks, and the full `detect_conflicts()` suite: time overload, impossible task, duplicate titles, time-slot clashes, and `"anytime"` tasks that never clash.
- **Sorting** — `sort_by_time()` orders `"HH:MM"` tasks chronologically with `"anytime"` tasks last, and preserves insertion order when all tasks are `"anytime"`.

### Confidence level

★★★★★ (5 / 5)

All 27 tests pass. Every public method on `Task`, `Pet`, and `Scheduler` is exercised by at least one test, including the trickiest edge cases (idempotent completion, recurring-task re-queuing, and multi-pet conflict detection). The only known gap is overlap-aware scheduling (a 30-min task at `07:00` overlapping a task at `07:20`) — this is a documented design tradeoff, not a defect.
