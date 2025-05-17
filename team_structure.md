
# Bluelabel AIOS – AI Team Strategy & Structure

This document outlines the team structure, naming conventions, responsibilities, and execution strategy for the AI-based development of Bluelabel AIOS.

---

## 🧠 Team Roster and Roles

| Role                  | Agent         | Short Name | Reports To | Responsibilities |
|-----------------------|---------------|------------|------------|------------------|
| Systems Architect     | ChatGPT       | Arch       | PM         | Maintains roadmap, task system, planning, alignment |
| Lead Developer        | Claude Code   | CC         | Arch       | Implements tasks from `TASK_CARDS.md`, manages execution |
| Dev Assistant         | Cursor AI     | CA         | CC         | Refactors, fills in glue code, scaffolds boilerplate |
| Prompt Engineer       | Windsurf AI   | WA         | Arch       | Develops prompt templates, handles LLM config/testing |
| Reviewer Agent        | Anthropic AI  | RA         | Arch       | Reviews code, flags deviations from plan/spec |
| Product Manager       | You           | PM         | —          | Sets direction, approves scope, defines milestones |

---

## 📦 Project Execution Workflow

1. All tasks originate from `TASK_CARDS.md` (or its `.csv` equivalent)
2. Tasks include: ID, Description, Acceptance Criteria, Technical Details
3. CC is the primary executor — CA and WA assist where delegated
4. RA reviews completed tasks using GitHub or repo snapshots
5. Arch coordinates agent interactions, manages planning and scope

---

## 🔁 High-Frequency Cadence

Bluelabel AIOS runs a high-speed async workflow. Traditional weekly sprints are replaced with **continuous micro-sprints**.

### ⏱ Execution Cycle

- **Arch** (ChatGPT) maintains task prioritization and tracks overall progress
- **You (PM)** set goals and validate results
- CC, CA, and WA can work in parallel — sometimes multiple tasks per day
- When a task is complete, it’s reviewed immediately, and the next task is assigned

### ✅ Agent Loop

1. **Pick task** from `TASK_CARDS.md` (`Status: Ready`)
2. **Update status** to `In Progress: [Agent]`
3. **Execute task**
4. **Push code with task ID**
5. **Mark as Done**
6. **RA (Anthropic)** reviews output and notifies Arch/PM

---

## 🔖 Naming Conventions

- **Branch name**: `feat/TASK-007-agent-runner`
- **Commit prefix**: `#TASK-007: implement agent runner`
- **Status labels**:
  - `Backlog`
  - `Ready`
  - `In Progress: CC`
  - `In Progress: CA`
  - `In Progress: WA`
  - `Reviewing: RA`
  - `Done`

---

## 📌 File Ownership

| File                   | Owner |
|------------------------|-------|
| `TASK_CARDS.md`        | Arch  |
| `README.md`            | CC    |
| `architecture.md`      | Arch  |
| `team_structure.md`    | Arch  |
| `IMPLEMENTATION_ROADMAP.md` | Archived (superseded) |
| `.env.example`, Docker | CC    |
| Prompt files, YAML     | WA    |
| Test coverage setup    | CA    |

---

## 🧭 Guidelines

- All agents should reference this file to understand roles and reporting
- PM and Arch handle strategic direction and assignment
- All execution flows through tasks — nothing off-road unless approved
- Coordination is async, tracked in markdown or CSV

