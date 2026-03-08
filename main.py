from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler, Priority, Frequency


# ---------------------------------------------------------------------------
# Setup — tasks deliberately added OUT OF TIME ORDER
# ---------------------------------------------------------------------------

mochi = Pet(name="Mochi", species="dog")
mochi.add_task(Task("Evening walk",      duration_minutes=25, priority=Priority.MEDIUM,
                    time_of_day="18:00"))
mochi.add_task(Task("Breakfast feeding", duration_minutes=10, priority=Priority.HIGH,
                    time_of_day="07:00"))
mochi.add_task(Task("Teeth brushing",    duration_minutes=5,  priority=Priority.MEDIUM,
                    time_of_day="08:30"))
mochi.add_task(Task("Afternoon nap",     duration_minutes=60, priority=Priority.LOW,
                    time_of_day="anytime"))
mochi.add_task(Task("Morning walk",      duration_minutes=30, priority=Priority.HIGH,
                    time_of_day="07:30"))

luna = Pet(name="Luna", species="cat")
luna.add_task(Task("Litter box clean",   duration_minutes=10, priority=Priority.HIGH,
                   time_of_day="08:00"))
luna.add_task(Task("Breakfast feeding",  duration_minutes=5,  priority=Priority.HIGH,
                   time_of_day="07:00"))
luna.add_task(Task("Grooming brush",     duration_minutes=15, priority=Priority.MEDIUM,
                   frequency=Frequency.WEEKLY, time_of_day="anytime"))
luna.add_task(Task("Evening play",       duration_minutes=10, priority=Priority.LOW,
                   time_of_day="19:30"))

jordan = Owner(name="Jordan", available_minutes=90)
jordan.add_pet(mochi)
jordan.add_pet(luna)

scheduler = Scheduler(jordan)

# ---------------------------------------------------------------------------
# 1. sort_by_time() — "HH:MM" string comparison orders chronologically
#    lambda key: (time_of_day == "anytime", time_of_day)
#    — False < True, so timed tasks always appear before "anytime" tasks
# ---------------------------------------------------------------------------

print("=" * 58)
print("1. ALL TASKS — sorted by time_of_day (earliest first)")
print("=" * 58)
print(f"  {'Time':>8}  {'Pet':<6}  {'Priority':<8}  Task")
print(f"  {'-'*8}  {'-'*6}  {'-'*8}  {'-'*25}")
for pet, task in scheduler.sort_by_time():
    time_label = task.time_of_day if task.time_of_day != "anytime" else "(anytime)"
    print(f"  {time_label:>9}  {pet.name:<6}  {task.priority.name:<8}  {task.title}")

# ---------------------------------------------------------------------------
# 2. filter_by_status() — mark a couple tasks complete first
# ---------------------------------------------------------------------------

mochi.tasks[1].mark_complete()   # Breakfast feeding (07:00) — done
luna.tasks[1].mark_complete()    # Breakfast feeding (07:00) — done

print()
print("=" * 58)
print("2a. FILTER — completed tasks")
print("=" * 58)
for pet, task in scheduler.filter_by_status(completed=True):
    print(f"  ✓ [{pet.name}] {task.title} @{task.time_of_day}")

print()
print("2b. FILTER — pending tasks")
print("=" * 58)
for pet, task in scheduler.filter_by_status(completed=False):
    time_label = task.time_of_day if task.time_of_day != "anytime" else "anytime"
    print(f"  ○ [{pet.name}] {task.title} @{time_label}")

# ---------------------------------------------------------------------------
# 3. filter_by_pet() — all tasks for one pet
# ---------------------------------------------------------------------------

print()
print("=" * 58)
print("3. FILTER — Mochi's tasks only")
print("=" * 58)
for task in scheduler.filter_by_pet("Mochi"):
    print(f"  {task}")

# ---------------------------------------------------------------------------
# 4. Conflict detection + final schedule
# ---------------------------------------------------------------------------

print()
print("=" * 58)
print("4. CONFLICT CHECK")
print("=" * 58)
conflicts = scheduler.detect_conflicts()
if conflicts:
    for c in conflicts:
        print(f"  ⚠  {c}")
else:
    print("  ✓  No conflicts detected.")

print()
print("=" * 58)
print("5. FINAL DAILY PLAN (pending tasks, priority order)")
print("=" * 58)
print(scheduler.summary())
print()
plan = scheduler.build_plan()
print(plan.display())
print(f"\nTotal scheduled: {plan.total_minutes()} / {jordan.available_minutes} min")

# ---------------------------------------------------------------------------
# 6. Recurrence — mark tasks complete and verify next occurrence is created
# ---------------------------------------------------------------------------

print()
print("=" * 58)
print("6. RECURRENCE — mark_task_complete() auto-enqueues next run")
print("=" * 58)

today = date.today()
print(f"   Today: {today}")
print()

# DAILY task — next due tomorrow
next_task = scheduler.mark_task_complete("Mochi", "Morning walk")
if next_task:
    print(f"  ✓ Completed: Morning walk (Mochi)")
    print(f"    → Next occurrence created: '{next_task.title}' due {next_task.due_date}")
    print(f"    → Offset from today: +{(next_task.due_date - today).days} day(s)")

print()

# WEEKLY task — next due in 7 days
next_task = scheduler.mark_task_complete("Luna", "Grooming brush")
if next_task:
    print(f"  ✓ Completed: Grooming brush (Luna)")
    print(f"    → Next occurrence created: '{next_task.title}' due {next_task.due_date}")
    print(f"    → Offset from today: +{(next_task.due_date - today).days} day(s)")

print()

# AS_NEEDED task — no next occurrence
mochi.add_task(Task("Vet visit", duration_minutes=60, priority=Priority.HIGH,
                    frequency=Frequency.AS_NEEDED))
next_task = scheduler.mark_task_complete("Mochi", "Vet visit")
print(f"  ✓ Completed: Vet visit (Mochi, AS_NEEDED)")
print(f"    → Next occurrence: {next_task!r}  (None — no auto-recurrence)")

print()
print("   Mochi's full task list after completions:")
for t in mochi.tasks:
    print(f"    {t}")

# ---------------------------------------------------------------------------
# 7. Time-clash conflict detection
# ---------------------------------------------------------------------------

print()
print("=" * 58)
print("7. TIME CLASH DETECTION")
print("=" * 58)

# Inject two tasks that share the same time slot
mochi.add_task(Task("Medication",    duration_minutes=5,  priority=Priority.HIGH,
                    time_of_day="07:30"))          # clashes with Morning walk @07:30
luna.add_task(Task("Morning feeding", duration_minutes=5, priority=Priority.HIGH,
                   time_of_day="07:30"))           # clashes with Mochi's tasks @07:30

print("   Added 'Medication' (Mochi @07:30) and 'Morning feeding' (Luna @07:30)")
print("   Both clash with existing Morning walk @07:30\n")

for conflict in scheduler.detect_conflicts():
    print(f"  ⚠  {conflict}")

# Show that removing one resolves the clash
mochi.remove_task("Medication")
luna.remove_task("Morning feeding")
print()
print("   After removing the conflicting tasks:")
clashes = [c for c in scheduler.detect_conflicts() if "clash" in c]
if clashes:
    for c in clashes:
        print(f"  ⚠  {c}")
else:
    print("  ✓  No time clashes detected.")
