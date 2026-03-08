# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The initial design centers on four classes with clear, separated responsibilities:

- **`Owner`** — stores the owner's name and total time available per day (in minutes). Acts as the entry point for a planning session.
- **`Pet`** — stores the pet's name and species. Owned by an `Owner` (composition).
- **`Task`** — represents a single care activity with a title, duration in minutes, and a priority level (`low`, `medium`, `high`). Pure data class; no scheduling logic.
- **`Scheduler`** — receives an `Owner` (and their `Pet`) plus a list of `Task` objects. Its `build_plan()` method applies constraints (total available time, task priority) to select and order tasks, returning a `DailyPlan`.
- **`DailyPlan`** — holds the ordered list of scheduled tasks and a human-readable explanation of why each task was included or excluded.

```mermaid
classDiagram
    class Owner {
        +str name
        +int available_minutes
        +Pet pet
    }

    class Pet {
        +str name
        +str species
    }

    class Task {
        +str title
        +int duration_minutes
        +str priority
    }

    class Scheduler {
        +Owner owner
        +list~Task~ tasks
        +build_plan() DailyPlan
    }

    class DailyPlan {
        +list~Task~ scheduled_tasks
        +list~str~ explanations
        +display() str
    }

    Owner "1" *-- "1" Pet : has
    Scheduler "1" --> "1" Owner : uses
    Scheduler "1" --> "0..*" Task : schedules
    Scheduler ..> DailyPlan : creates
```

**b. Design changes**

The design has not yet changed from the initial version — implementation is still in progress. One anticipated change is splitting `priority` out of `Task` into a separate `Priority` enum (`LOW`, `MEDIUM`, `HIGH`) so comparisons in the scheduler are type-safe rather than string-based. Another likely change is adding a `time_of_day` preference field to `Task` (e.g., `morning`, `afternoon`, `anytime`) once time-slot ordering becomes a requirement.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
