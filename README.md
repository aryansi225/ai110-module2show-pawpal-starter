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
