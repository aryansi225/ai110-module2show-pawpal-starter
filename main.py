from pawpal_system import Owner, Pet, Task, Scheduler, Priority, Frequency


# --- Setup -----------------------------------------------------------------

mochi = Pet(name="Mochi", species="dog")
mochi.add_task(Task("Morning walk",      duration_minutes=30, priority=Priority.HIGH))
mochi.add_task(Task("Breakfast feeding", duration_minutes=10, priority=Priority.HIGH))
mochi.add_task(Task("Teeth brushing",    duration_minutes=5,  priority=Priority.MEDIUM))
mochi.add_task(Task("Fetch / play time", duration_minutes=20, priority=Priority.LOW))

luna = Pet(name="Luna", species="cat")
luna.add_task(Task("Breakfast feeding",  duration_minutes=5,  priority=Priority.HIGH))
luna.add_task(Task("Litter box clean",   duration_minutes=10, priority=Priority.HIGH))
luna.add_task(Task("Grooming brush",     duration_minutes=15, priority=Priority.MEDIUM,
                   frequency=Frequency.WEEKLY))

jordan = Owner(name="Jordan", available_minutes=75)
jordan.add_pet(mochi)
jordan.add_pet(luna)

# --- Schedule --------------------------------------------------------------

scheduler = Scheduler(jordan)
print(scheduler.summary())
print()

plan = scheduler.build_plan()
print(plan.display())
print(f"\nTotal scheduled time: {plan.total_minutes()} / {jordan.available_minutes} min")
