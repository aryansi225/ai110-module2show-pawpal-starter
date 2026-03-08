import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, Priority, Frequency, DailyPlan

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None

# ---------------------------------------------------------------------------
# Section 1 – Owner & first pet profile
# ---------------------------------------------------------------------------

st.header("1. Owner & Pet Profile")

with st.form("profile_form"):
    owner_name     = st.text_input("Your name", value="Jordan")
    available_mins = st.number_input("Minutes available today", min_value=10, max_value=480, value=60, step=5)
    pet_name       = st.text_input("First pet's name", value="Mochi")
    species        = st.selectbox("Species", ["dog", "cat", "other"])
    save_profile   = st.form_submit_button("Save profile")

if save_profile:
    # Owner() + Pet() constructed here; owner.add_pet() links them
    pet   = Pet(name=pet_name, species=species)
    owner = Owner(name=owner_name, available_minutes=int(available_mins))
    owner.add_pet(pet)                          # <-- Owner.add_pet()
    st.session_state.owner = owner
    st.success(f"Profile saved — {owner_name} with {pet_name} ({species}), {available_mins} min available.")

# Guard: nothing below renders until a profile exists
if st.session_state.owner is None:
    st.info("Fill in the profile above and click **Save profile** to get started.")
    st.stop()

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Section 1b – Add another pet
# ---------------------------------------------------------------------------

with st.expander("Add another pet"):
    with st.form("add_pet_form"):
        new_pet_name    = st.text_input("New pet's name", value="Luna")
        new_pet_species = st.selectbox("Species", ["dog", "cat", "other"], key="new_species")
        add_pet_submit  = st.form_submit_button("Add pet")

    if add_pet_submit:
        if owner.get_pet(new_pet_name):               # guard against duplicates
            st.warning(f"A pet named '{new_pet_name}' already exists.")
        else:
            owner.add_pet(Pet(name=new_pet_name, species=new_pet_species))  # <-- Owner.add_pet()
            st.success(f"Added {new_pet_name} ({new_pet_species}).")

# Show pets registered so far
st.caption("Registered pets: " + ", ".join(f"**{p.name}** ({p.species})" for p in owner.pets))

# ---------------------------------------------------------------------------
# Section 2 – Add tasks
# ---------------------------------------------------------------------------

st.divider()
st.header("2. Manage Tasks")

pet_names   = [p.name for p in owner.pets]
target_name = st.selectbox("Pet", pet_names, key="task_target")
target_pet  = owner.get_pet(target_name)           # <-- Owner.get_pet()

# -- Add task ---------------------------------------------------------------
with st.form("task_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority_str = st.selectbox("Priority", ["HIGH", "MEDIUM", "LOW"])
    add_task = st.form_submit_button("Add task")

if add_task and target_pet is not None:
    target_pet.add_task(                            # <-- Pet.add_task()
        Task(title=task_title, duration_minutes=int(duration), priority=Priority[priority_str])
    )
    st.success(f"Added '{task_title}' to {target_name}.")

# -- Current task table with mark-complete + remove -------------------------
all_tasks = owner.all_tasks()                       # <-- Owner.all_tasks()
if all_tasks:
    st.markdown("**Current tasks:**")
    for i, (pet, task) in enumerate(all_tasks):
        col_info, col_done, col_del = st.columns([5, 1, 1])
        with col_info:
            status = "✓" if task.completed else "○"
            st.markdown(
                f"{status} **[{pet.name}]** {task.title} — "
                f"{task.duration_minutes} min | {task.priority.name}"
            )
        with col_done:
            if not task.completed:
                if st.button("Done", key=f"done_{i}"):
                    task.mark_complete()            # <-- Task.mark_complete()
                    st.rerun()
        with col_del:
            if st.button("✕", key=f"del_{i}"):
                pet.remove_task(task.title)         # <-- Pet.remove_task()
                st.rerun()
else:
    st.info("No tasks yet. Add one above.")

# -- Sorted pending tasks view -----------------------------------------------
scheduler_preview = Scheduler(owner)                # <-- Scheduler.__init__()
pending_sorted = scheduler_preview.pending_tasks_by_priority()  # <-- Scheduler.pending_tasks_by_priority()
if pending_sorted:
    with st.expander("View pending tasks sorted by priority"):
        rows = [
            {
                "Pet": pet.name,
                "Task": task.title,
                "Priority": task.priority.name,
                "Duration (min)": task.duration_minutes,
                "Time of Day": task.time_of_day,
            }
            for pet, task in pending_sorted
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)

# -- Conflict warnings -------------------------------------------------------
conflicts = scheduler_preview.detect_conflicts()    # <-- Scheduler.detect_conflicts()
if conflicts:
    st.markdown("**Scheduling conflicts detected:**")
    for conflict in conflicts:
        if "Impossible task" in conflict:
            st.error(f"**Cannot schedule:** {conflict}")
        elif "Time clash" in conflict:
            st.warning(
                f"**Time clash:** {conflict}\n\n"
                "_Two tasks are assigned the same start time. "
                "Edit one task's time-of-day to resolve._"
            )
        elif "Duplicate task" in conflict:
            st.warning(f"**Duplicate:** {conflict}")
        else:
            st.warning(f"**Warning:** {conflict}")

# -- Reset daily tasks -------------------------------------------------------
if st.button("Reset all daily tasks (new day)"):
    for pet in owner.pets:
        pet.reset_daily_tasks()                     # <-- Pet.reset_daily_tasks()
    st.success("All daily tasks reset.")
    st.rerun()

# ---------------------------------------------------------------------------
# Section 3 – Generate schedule
# ---------------------------------------------------------------------------

st.divider()
st.header("3. Today's Schedule")

if st.button("Generate schedule"):
    scheduler = Scheduler(owner)                    # <-- Scheduler.__init__()
    plan      = scheduler.build_plan()              # <-- Scheduler.build_plan()

    st.info(scheduler.summary())                    # <-- Scheduler.summary()

    # Show any conflicts prominently before the plan so the owner can act on them
    conflicts = scheduler.detect_conflicts()        # <-- Scheduler.detect_conflicts()
    for conflict in conflicts:
        if "Impossible task" in conflict:
            st.error(f"Cannot schedule: {conflict}")
        elif "Time clash" in conflict:
            st.warning(
                f"**Time clash warning:** {conflict}\n\n"
                "_Edit one of the conflicting tasks' time-of-day to resolve._"
            )
        elif "Duplicate task" in conflict:
            st.warning(f"Duplicate task detected: {conflict}")
        else:
            st.warning(conflict)

    st.divider()

    if plan.scheduled:
        st.subheader("Scheduled tasks")
        cumulative = 0
        rows = []
        for pet, task in plan.scheduled:
            cumulative += task.duration_minutes
            rows.append({
                "Pet": pet.name,
                "Task": task.title,
                "Priority": task.priority.name,
                "Duration (min)": task.duration_minutes,
                "Running Total (min)": cumulative,
                "Time of Day": task.time_of_day,
            })
        st.table(rows)
        st.success(
            f"Scheduled {len(plan.scheduled)} task(s) — "
            f"{plan.total_minutes()} / {owner.available_minutes} min used."  # <-- DailyPlan.total_minutes()
        )
    else:
        st.warning("No tasks fit within the available time.")

    if plan.skipped:
        st.subheader("Skipped tasks")
        for pet, task, reason in plan.skipped:
            st.warning(
                f"**[{pet.name}] {task.title}** skipped — {reason}\n\n"
                "_Consider reducing this task's duration or freeing up more time._"
            )
