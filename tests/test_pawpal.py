from pawpal_system import Task, Pet, Owner, Scheduler, Priority, Frequency


# ---------------------------------------------------------------------------
# Task tests
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
# Pet tests
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
# Scheduler tests
# ---------------------------------------------------------------------------

def test_scheduler_skips_tasks_that_exceed_available_time():
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Long hike", duration_minutes=120, priority=Priority.LOW))
    owner = Owner(name="Jordan", available_minutes=30, pets=[pet])
    plan = Scheduler(owner).build_plan()
    assert len(plan.scheduled) == 0
    assert len(plan.skipped) == 1


def test_scheduler_prioritises_high_priority_tasks_first():
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Play time",  duration_minutes=20, priority=Priority.LOW))
    pet.add_task(Task("Medication", duration_minutes=5,  priority=Priority.HIGH))
    owner = Owner(name="Jordan", available_minutes=20, pets=[pet])
    plan = Scheduler(owner).build_plan()
    # Medication (HIGH) should be scheduled; Play time (LOW) should be skipped
    scheduled_titles = [t.title for _, t in plan.scheduled]
    assert "Medication" in scheduled_titles
    assert "Play time" not in scheduled_titles


def test_scheduler_completed_tasks_are_excluded_from_plan():
    pet = Pet(name="Luna", species="cat")
    task = Task("Feeding", duration_minutes=5, priority=Priority.HIGH)
    task.mark_complete()
    pet.add_task(task)
    owner = Owner(name="Jordan", available_minutes=60, pets=[pet])
    plan = Scheduler(owner).build_plan()
    assert len(plan.scheduled) == 0
