"""Render the final PawPal+ UML class diagram to uml_final.png using matplotlib."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
FIG_W, FIG_H = 22, 16
BOX_PAD   = 0.18      # internal padding inside each box (inches)
FONT_NAME = 14        # name section font size
FONT_ATTR = 10        # attributes / methods font size
HEADER_H  = 0.52      # height of the «stereotype» + name header row
ROW_H     = 0.30      # height per attribute/method line

ENUM_COLOR   = "#EFF6FF"   # light blue tint for enums
CLASS_COLOR  = "#F0FDF4"   # light green tint for classes
BORDER       = "#374151"
HEADER_FILL  = "#1E3A5F"   # dark navy header band
ENUM_HEADER  = "#1E3A8A"
DIVIDER      = "#9CA3AF"
TEXT_LIGHT   = "white"
TEXT_DARK    = "#111827"
METHOD_COLOR = "#1D4ED8"   # blue for method names
ATTR_COLOR   = "#374151"

# ---------------------------------------------------------------------------
# Helper: draw one class/enum box, return (x, y, w, h) of the outer rect
# ---------------------------------------------------------------------------

def draw_box(ax, cx, cy, name, stereotype, attributes, methods,
             box_color=CLASS_COLOR, hdr_color=HEADER_FILL):
    """
    Draw a UML class box centred at (cx, cy).
    Returns (left, bottom, width, total_height).
    """
    n_attr = len(attributes)
    n_meth = len(methods)

    # Calculate widths
    all_text = (
        [name] +
        [f"  {a}" for a in attributes] +
        [f"  {m}" for m in methods]
    )
    max_chars = max(len(t) for t in all_text)
    box_w = max(2.4, max_chars * 0.095 + 0.4)

    # Calculate heights
    hdr_h   = HEADER_H
    attr_h  = n_attr * ROW_H if n_attr else ROW_H * 0.5
    meth_h  = n_meth * ROW_H if n_meth else 0
    total_h = hdr_h + attr_h + (ROW_H * 0.25 if n_meth else 0) + meth_h

    left   = cx - box_w / 2
    bottom = cy - total_h / 2

    # Outer border
    rect = mpatches.FancyBboxPatch(
        (left, bottom), box_w, total_h,
        boxstyle="round,pad=0.04",
        linewidth=1.5, edgecolor=BORDER, facecolor=box_color, zorder=2
    )
    ax.add_patch(rect)

    # Header band
    hdr_rect = mpatches.Rectangle(
        (left, bottom + total_h - hdr_h), box_w, hdr_h,
        linewidth=0, facecolor=hdr_color, zorder=3
    )
    ax.add_patch(hdr_rect)

    # Stereotype label
    if stereotype:
        ax.text(cx, bottom + total_h - hdr_h * 0.28,
                f"«{stereotype}»",
                ha="center", va="center", fontsize=8, color="#BFDBFE",
                zorder=4, style="italic")
    # Class name
    name_y = bottom + total_h - hdr_h * 0.72 if stereotype else bottom + total_h - hdr_h * 0.5
    ax.text(cx, name_y, name,
            ha="center", va="center", fontsize=FONT_NAME,
            fontweight="bold", color=TEXT_LIGHT, zorder=4)

    # Divider below header
    div_y = bottom + total_h - hdr_h
    ax.plot([left, left + box_w], [div_y, div_y],
            color=DIVIDER, linewidth=1, zorder=4)

    # Attributes
    for i, attr in enumerate(attributes):
        ay = bottom + total_h - hdr_h - ROW_H * (i + 0.65)
        ax.text(left + 0.12, ay, attr,
                ha="left", va="center", fontsize=FONT_ATTR,
                color=ATTR_COLOR, zorder=4, family="monospace")

    # Divider before methods
    if n_meth:
        sep_y = bottom + total_h - hdr_h - attr_h - ROW_H * 0.12
        ax.plot([left, left + box_w], [sep_y, sep_y],
                color=DIVIDER, linewidth=0.8, linestyle="--", zorder=4)
        for j, meth in enumerate(methods):
            my = sep_y - ROW_H * (j + 0.65)
            ax.text(left + 0.12, my, meth,
                    ha="left", va="center", fontsize=FONT_ATTR,
                    color=METHOD_COLOR, zorder=4, family="monospace")

    return left, bottom, box_w, total_h


# ---------------------------------------------------------------------------
# Helper: arrow
# ---------------------------------------------------------------------------

def arrow(ax, x1, y1, x2, y2, style="->", color="#374151", label="", lw=1.4):
    arrowprops = dict(
        arrowstyle=style,
        color=color,
        lw=lw,
        connectionstyle="arc3,rad=0.0",
    )
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=arrowprops, zorder=5)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.08, my + 0.08, label,
                fontsize=8, color="#6B7280", zorder=6, style="italic")


# ---------------------------------------------------------------------------
# Build the figure
# ---------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis("off")
fig.patch.set_facecolor("#F9FAFB")

# Title
ax.text(FIG_W / 2, FIG_H - 0.45, "PawPal+ — Final UML Class Diagram",
        ha="center", va="center", fontsize=18, fontweight="bold",
        color=HEADER_FILL)
ax.text(FIG_W / 2, FIG_H - 0.85,
        "Reflects final pawpal_system.py implementation",
        ha="center", va="center", fontsize=11, color="#6B7280", style="italic")

# ---------------------------------------------------------------------------
# Positions  (cx, cy)
# ---------------------------------------------------------------------------

# Row 1 (top): enums
PRI_X, PRI_Y   = 3.2,  13.2
FREQ_X, FREQ_Y = 7.0,  13.2

# Row 2: Task, Pet
TASK_X, TASK_Y  = 3.2,  9.8
PET_X,  PET_Y   = 8.8,  9.4

# Row 3: Owner, DailyPlan
OWN_X,  OWN_Y   = 8.8,  5.2
PLAN_X, PLAN_Y  = 16.5, 9.4

# Row 4: Scheduler (centre)
SCH_X,  SCH_Y   = 13.0, 5.8

# ---------------------------------------------------------------------------
# Draw boxes
# ---------------------------------------------------------------------------

# Priority enum
p_l, p_b, p_w, p_h = draw_box(
    ax, PRI_X, PRI_Y, "Priority", "enumeration",
    ["LOW = 1", "MEDIUM = 2", "HIGH = 3"], [],
    box_color=ENUM_COLOR, hdr_color=ENUM_HEADER
)

# Frequency enum
f_l, f_b, f_w, f_h = draw_box(
    ax, FREQ_X, FREQ_Y, "Frequency", "enumeration",
    ["DAILY", "WEEKLY", "AS_NEEDED"], [],
    box_color=ENUM_COLOR, hdr_color=ENUM_HEADER
)

# Task
t_l, t_b, t_w, t_h = draw_box(
    ax, TASK_X, TASK_Y, "Task", None,
    [
        "+title : str",
        "+duration_minutes : int",
        "+priority : Priority",
        "+frequency : Frequency",
        "+completed : bool",
        "+time_of_day : str",
        "+due_date : date",
    ],
    [
        "+mark_complete() : None",
        "+reset() : None",
        "+next_occurrence() : Task",
    ]
)

# Pet
pet_l, pet_b, pet_w, pet_h = draw_box(
    ax, PET_X, PET_Y, "Pet", None,
    ["+name : str", "+species : str", "+tasks : list[Task]"],
    [
        "+add_task(task) : None",
        "+remove_task(title) : bool",
        "+get_pending_tasks() : list",
        "+get_completed_tasks() : list",
        "+reset_daily_tasks() : None",
        "+total_task_minutes() : int",
    ]
)

# Owner
own_l, own_b, own_w, own_h = draw_box(
    ax, OWN_X, OWN_Y, "Owner", None,
    ["+name : str", "+available_minutes : int", "+pets : list[Pet]"],
    [
        "+add_pet(pet) : None",
        "+remove_pet(name) : bool",
        "+get_pet(name) : Pet",
        "+all_tasks() : list",
        "+all_pending_tasks() : list",
        "+total_pending_minutes() : int",
    ]
)

# DailyPlan
dp_l, dp_b, dp_w, dp_h = draw_box(
    ax, PLAN_X, PLAN_Y, "DailyPlan", None,
    [
        "+scheduled : list[(Pet,Task)]",
        "+skipped : list[(Pet,Task,str)]",
    ],
    [
        "+display() : str",
        "+total_minutes() : int",
    ]
)

# Scheduler
sch_l, sch_b, sch_w, sch_h = draw_box(
    ax, SCH_X, SCH_Y, "Scheduler", None,
    ["+owner : Owner"],
    [
        "+build_plan() : DailyPlan",
        "+build_plan_for_pet(name) : DailyPlan",
        "+pending_tasks_by_priority() : list",
        "+high_priority_tasks() : list",
        "+sort_by_time() : list",
        "+tasks_sorted_by_duration(asc) : list",
        "+filter_by_pet(name) : list",
        "+filter_by_status(completed) : list",
        "+due_today() : list",
        "+detect_conflicts() : list[str]",
        "+mark_task_complete(pet,title) : Task",
        "+summary() : str",
    ]
)

# ---------------------------------------------------------------------------
# Arrows
# ---------------------------------------------------------------------------

# Task --> Priority  (uses)
arrow(ax, TASK_X + t_w/2, TASK_Y + 0.9, PRI_X, PRI_Y - p_h/2,
      style="->", color="#3B82F6", label="uses")

# Task --> Frequency  (uses)
arrow(ax, TASK_X + t_w/2, TASK_Y + 0.5, FREQ_X - f_w/2, FREQ_Y - 0.3,
      style="->", color="#3B82F6", label="uses")

# Pet *-- Task  (composition: Pet owns Tasks)
arrow(ax, PET_X - pet_w/2, PET_Y + 0.3, TASK_X + t_w/2, TASK_Y + 0.3,
      style="-|>", color="#059669", label="1 owns 0..*")

# Owner *-- Pet  (composition: Owner owns Pets)
arrow(ax, OWN_X - own_w/2, OWN_Y + 0.2, PET_X, PET_Y - pet_h/2,
      style="-|>", color="#059669", label="1 owns 1..*")

# Scheduler --> Owner  (reads)
arrow(ax, SCH_X - sch_w/2, SCH_Y + 0.6, OWN_X + own_w/2, OWN_Y + 0.6,
      style="->", color=BORDER, label="reads")

# Scheduler ..> DailyPlan  (creates)
arrow(ax, SCH_X + sch_w/2, SCH_Y + 1.2, PLAN_X - dp_w/2, PLAN_Y - 0.4,
      style="->", color="#7C3AED", label="creates")

# DailyPlan --> Pet/Task  (references — single label on the box)
ax.text(PLAN_X - dp_w/2 - 0.15, PLAN_Y - dp_h/2 - 0.25,
        "references Pet & Task tuples",
        fontsize=8, color="#6B7280", style="italic", ha="center")

# ---------------------------------------------------------------------------
# Legend
# ---------------------------------------------------------------------------
legend_x, legend_y = 0.4, 2.1
ax.text(legend_x, legend_y + 0.5, "Legend", fontsize=10,
        fontweight="bold", color=TEXT_DARK)
items = [
    ("#059669", "─▷  Composition (owns)"),
    ("#3B82F6", "──▶  Uses / dependency"),
    ("#7C3AED", "──▶  Creates"),
    (BORDER,    "──▶  Association / reads"),
]
for i, (color, label) in enumerate(items):
    ax.plot([legend_x, legend_x + 0.5], [legend_y - i * 0.32, legend_y - i * 0.32],
            color=color, lw=2)
    ax.text(legend_x + 0.6, legend_y - i * 0.32, label,
            fontsize=9, va="center", color=TEXT_DARK)

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
plt.tight_layout(pad=0.5)
plt.savefig("uml_final.png", dpi=150, bbox_inches="tight",
            facecolor=fig.get_facecolor())
print("Saved uml_final.png")
