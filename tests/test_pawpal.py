from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler, Priority, Frequency


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_owner(minutes=60, *pets):
    """Return an Owner with the given pets and available_minutes."""
    return Owner(name="Jordan", available_minutes=minutes, pets=list(pets))


# ---------------------------------------------------------------------------
# Task — happy paths
# ---------------------------------------------------------------------------

def test_task_defaults_to_not_completed():
    task = Task("Morning walk", duration_minutes=30, priority=Priority.HIGH)
    assert task.completed is False


def test_mark_complete_sets_completed_true():
    task = Task("Morning walk", duration_minutes=30, priority=Priority.HIGH)
    task.mark_complete()
    assert task.completed is True


def test_reset_clears_completed_status():
    task = Task("Morning walk", duration_minutes=30, priority=Priority.HIGH)
    task.mark_complete()
    task.reset()
    assert task.completed is False


# ---------------------------------------------------------------------------
# Task — recurring / next_occurrence
# ---------------------------------------------------------------------------

def test_daily_task_next_occurrence_is_tomorrow():
    today = date.today()
    task = Task("Walk", duration_minutes=20, priority=Priority.HIGH,
                frequency=Frequency.DAILY, due_date=today)
    nxt = task.next_occurrence()
    assert nxt is not None
    assert nxt.due_date == today + timedelta(days=1)
    assert nxt.completed is False


def test_weekly_task_next_occurrence_is_seven_days_later():
    today = date.today()
    task = Task("Grooming", duration_minutes=15, priority=Priority.MEDIUM,
                frequency=Frequency.WEEKLY, due_date=today)
    nxt = task.next_occurrence()
    assert nxt is not None
    assert nxt.due_date == today + timedelta(weeks=1)


def test_as_needed_task_next_occurrence_is_none():
    task = Task("Vet visit", duration_minutes=60, priority=Priority.HIGH,
                frequency=Frequency.AS_NEEDED)
    assert task.next_occurrence() is None


def test_next_occurrence_preserves_title_and_duration():
    task = Task("Feeding", duration_minutes=10, priority=Priority.HIGH,
                frequency=Frequency.DAILY, time_of_day="07:00")
    nxt = task.next_occurrence()
    assert nxt.title == "Feeding"
    assert nxt.duration_minutes == 10
    assert nxt.time_of_day == "07:00"


# ---------------------------------------------------------------------------
# Task — edge cases
# ---------------------------------------------------------------------------

def test_marking_already_completed_task_stays_completed():
    task = Task("Walk", duration_minutes=20, priority=Priority.HIGH)
    task.mark_complete()
    task.mark_complete()  # calling twice should be idempotent
    assert task.completed is True


# ---------------------------------------------------------------------------
# Pet — happy paths
# ---------------------------------------------------------------------------

def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0
    pet.add_task(Task("Feeding", duration_minutes=10, priority=Priority.HIGH))
    assert len(pet.tasks) == 1
    pet.add_task(Task("Walk", duration_minutes=20, priority=Priority.MEDIUM))
    assert len(pet.tasks) == 2


def test_remove_task_decreases_pet_task_count():
    pet = Pet(name="Luna", species="cat")
    pet.add_task(Task("Feeding", duration_minutes=5, priority=Priority.HIGH))
    removed = pet.remove_task("Feeding")
    assert removed is True
    assert len(pet.tasks) == 0


def test_remove_task_returns_false_when_not_found():
    pet = Pet(name="Luna", species="cat")
    assert pet.remove_task("Nonexistent") is False


def test_get_pending_tasks_excludes_completed():
    pet = Pet(name="Mochi", species="dog")
    t1 = Task("Walk", duration_minutes=30, priority=Priority.HIGH)
    t2 = Task("Feeding", duration_minutes=10, priority=Priority.HIGH)
    pet.add_task(t1)
    pet.add_task(t2)
    t1.mark_complete()
    pending = pet.get_pending_tasks()
    assert len(pending) == 1
    assert pending[0].title == "Feeding"


# ---------------------------------------------------------------------------
# Pet — edge cases
# ---------------------------------------------------------------------------

def test_pet_with_no_tasks_has_empty_pending_list():
    pet = Pet(name="Ghost", species="cat")
    assert pet.get_pending_tasks() == []
    assert pet.get_completed_tasks() == []
    assert pet.total_task_minutes() == 0


def test_reset_daily_tasks_only_clears_daily_not_weekly():
    pet = Pet(name="Luna", species="cat")
    daily = Task("Feeding", duration_minutes=5,  priority=Priority.HIGH,
                 frequency=Frequency.DAILY)
    weekly = Task("Grooming", duration_minutes=15, priority=Priority.MEDIUM,
                  frequency=Frequency.WEEKLY)
    daily.mark_complete()
    weekly.mark_complete()
    pet.add_task(daily)
    pet.add_task(weekly)
    pet.reset_daily_tasks()
    assert daily.completed is False   # DAILY reset
    assert weekly.completed is True   # WEEKLY untouched


# ---------------------------------------------------------------------------
# Scheduler — happy paths
# ---------------------------------------------------------------------------

def test_scheduler_skips_tasks_that_exceed_available_time():
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Long hike", duration_minutes=120, priority=Priority.LOW))
    owner = make_owner(30, pet)
    plan = Scheduler(owner).build_plan()
    assert len(plan.scheduled) == 0
    assert len(plan.skipped) == 1


def test_scheduler_prioritises_high_priority_tasks_first():
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Play time",  duration_minutes=20, priority=Priority.LOW))
    pet.add_task(Task("Medication", duration_minutes=5,  priority=Priority.HIGH))
    owner = make_owner(20, pet)
    plan = Scheduler(owner).build_plan()
    scheduled_titles = [t.title for _, t in plan.scheduled]
    assert "Medication" in scheduled_titles
    assert "Play time" not in scheduled_titles


def test_scheduler_completed_tasks_are_excluded_from_plan():
    pet = Pet(name="Luna", species="cat")
    task = Task("Feeding", duration_minutes=5, priority=Priority.HIGH)
    task.mark_complete()
    pet.add_task(task)
    owner = make_owner(60, pet)
    plan = Scheduler(owner).build_plan()
    assert len(plan.scheduled) == 0


def test_mark_task_complete_enqueues_next_daily_occurrence():
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk", duration_minutes=20, priority=Priority.HIGH,
                      frequency=Frequency.DAILY))
    owner = make_owner(60, pet)
    before_count = len(pet.tasks)
    Scheduler(owner).mark_task_complete("Mochi", "Walk")
    assert len(pet.tasks) == before_count + 1
    assert pet.tasks[-1].completed is False
    assert pet.tasks[-1].due_date == date.today() + timedelta(days=1)


def test_sort_by_time_orders_tasks_chronologically():
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Evening walk",   duration_minutes=25, priority=Priority.MEDIUM,
                      time_of_day="18:00"))
    pet.add_task(Task("Breakfast",      duration_minutes=10, priority=Priority.HIGH,
                      time_of_day="07:00"))
    pet.add_task(Task("Free play",      duration_minutes=15, priority=Priority.LOW,
                      time_of_day="anytime"))
    pet.add_task(Task("Morning walk",   duration_minutes=30, priority=Priority.HIGH,
                      time_of_day="07:30"))
    owner = make_owner(120, pet)
    sorted_tasks = [t.time_of_day for _, t in Scheduler(owner).sort_by_time()]
    assert sorted_tasks == ["07:00", "07:30", "18:00", "anytime"]


# ---------------------------------------------------------------------------
# Scheduler — edge cases
# ---------------------------------------------------------------------------

def test_scheduler_with_no_pets_produces_empty_plan():
    owner = Owner(name="Jordan", available_minutes=60)
    plan = Scheduler(owner).build_plan()
    assert len(plan.scheduled) == 0
    assert len(plan.skipped) == 0


def test_scheduler_with_pet_that_has_no_tasks_produces_empty_plan():
    pet = Pet(name="Ghost", species="cat")
    owner = make_owner(60, pet)
    plan = Scheduler(owner).build_plan()
    assert len(plan.scheduled) == 0


def test_detect_conflicts_time_clash_same_slot():
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk",     duration_minutes=20, priority=Priority.HIGH,
                      time_of_day="07:30"))
    pet.add_task(Task("Feeding",  duration_minutes=10, priority=Priority.HIGH,
                      time_of_day="07:30"))
    owner = make_owner(60, pet)
    conflicts = Scheduler(owner).detect_conflicts()
    assert any("clash" in c for c in conflicts)


def test_detect_conflicts_no_clash_different_slots():
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk",    duration_minutes=20, priority=Priority.HIGH,
                      time_of_day="07:00"))
    pet.add_task(Task("Feeding", duration_minutes=10, priority=Priority.HIGH,
                      time_of_day="08:00"))
    owner = make_owner(60, pet)
    conflicts = Scheduler(owner).detect_conflicts()
    assert not any("clash" in c for c in conflicts)


def test_detect_conflicts_anytime_tasks_do_not_clash():
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Play",    duration_minutes=15, priority=Priority.LOW,
                      time_of_day="anytime"))
    pet.add_task(Task("Nap",     duration_minutes=60, priority=Priority.LOW,
                      time_of_day="anytime"))
    owner = make_owner(120, pet)
    conflicts = Scheduler(owner).detect_conflicts()
    assert not any("clash" in c for c in conflicts)


def test_detect_conflicts_duplicate_task_title():
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk", duration_minutes=20, priority=Priority.HIGH))
    pet.add_task(Task("Walk", duration_minutes=20, priority=Priority.HIGH))
    owner = make_owner(60, pet)
    conflicts = Scheduler(owner).detect_conflicts()
    assert any("Duplicate" in c for c in conflicts)


def test_sort_by_time_all_anytime_tasks_returns_stable_order():
    pet = Pet(name="Luna", species="cat")
    pet.add_task(Task("A", duration_minutes=5,  priority=Priority.HIGH,  time_of_day="anytime"))
    pet.add_task(Task("B", duration_minutes=10, priority=Priority.MEDIUM, time_of_day="anytime"))
    owner = make_owner(60, pet)
    result = Scheduler(owner).sort_by_time()
    # All anytime — order should be preserved (stable sort)
    titles = [t.title for _, t in result]
    assert titles == ["A", "B"]


def test_mark_task_complete_does_not_re_complete_already_done_task():
    pet = Pet(name="Mochi", species="dog")
    task = Task("Walk", duration_minutes=20, priority=Priority.HIGH,
                frequency=Frequency.DAILY)
    task.mark_complete()
    pet.add_task(task)
    owner = make_owner(60, pet)
    count_before = len(pet.tasks)
    result = Scheduler(owner).mark_task_complete("Mochi", "Walk")
    # Already completed — should not enqueue another occurrence
    assert result is None
    assert len(pet.tasks) == count_before
