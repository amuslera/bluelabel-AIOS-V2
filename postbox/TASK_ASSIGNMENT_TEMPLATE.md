# Task Assignment Template

## IMPORTANT: Task Assignment Guidelines

### 1. File Placement
- Tasks FOR an agent go in: `postbox/{AGENT}/inbox/`
- Responses FROM an agent go in: `postbox/{AGENT}/outbox/`
- NEVER put a task in the wrong agent's inbox

### 2. File Naming Convention
- Use descriptive names: `{TASK_TYPE}_{PRIORITY}_{DATE}.md`
- Example: `ROI_WORKFLOW_UI_HIGH_20250130.md`

### 3. Required Header Format
Every task assignment MUST include:

```markdown
# [Task Title]

## TO: [Agent Name] ([Agent Role])
## FROM: [Sender] ([Sender Role])
## DATE: YYYY-MM-DD
## Priority: [HIGH|MEDIUM|LOW]
## Status: [IMMEDIATE ACTION REQUIRED|PENDING|IN PROGRESS]

[Clear task description...]
```

### 4. Agent Directory
- CA: UI/Frontend Implementation
- CB: Backend/API Development  
- CC: Claude Code (Code Review/Integration)
- ARCH: Architecture/Orchestration
- WA: WhatsApp Integration

### 5. Task Clarity Rules
- Start with "Your Tasks:" section
- Use numbered lists for multiple tasks
- Include acceptance criteria
- Specify deadlines if applicable
- Reference related files/endpoints

### Example Task Assignment:

```markdown
# Implement User Authentication UI

## TO: CA (UI Implementation Agent)
## FROM: ARCH (Architecture Agent)
## DATE: 2025-01-30
## Priority: HIGH
## Status: IMMEDIATE ACTION REQUIRED

We need login/signup screens for the new authentication system.

## Your Tasks:

1. Create Login Component
   - Email/password fields
   - Remember me checkbox
   - Forgot password link
   - Connect to `/api/auth/login`

2. Create Signup Component  
   - Email, password, confirm password
   - Terms acceptance checkbox
   - Connect to `/api/auth/register`

## Acceptance Criteria:
- Forms validate on submit
- Show loading states
- Display API errors
- Redirect on success

## Related Files:
- API docs: `/docs/api/auth.md`
- Design mockups: `/design/auth-screens.fig`

Please complete by end of day.
```

## Common Mistakes to Avoid:
❌ Putting tasks in the sender's inbox instead of recipient's
❌ Using "From: [Same Agent]" in a task assignment
❌ Unclear or missing TO/FROM headers
❌ Not specifying concrete deliverables
❌ Missing priority or status

## Verification Checklist:
- [ ] Is the file in the correct agent's inbox?
- [ ] Does the TO field match the inbox location?
- [ ] Are the tasks clearly defined?
- [ ] Is the priority set appropriately?
- [ ] Are all related resources referenced?