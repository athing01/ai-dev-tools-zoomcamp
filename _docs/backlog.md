# MVP Backlog

## 1. Household chores domain model and migrations

**Goal:** Add the persistent Django models needed for members, weekly rounds, chores, per-round chore state/assignment, readiness confirmations, and chore selections.

**Acceptance criteria:**

- Supports one household only, with members identified by name.
- Keeps a distinct weekly-round record and per-round chore records so historical assignments/statuses are never overwritten.
- Supports `Pending`, `Assigned`, and `Completed` chore states.
- Supports selections and readiness confirmations for a particular round and allocation phase.
- Creates and applies Django migrations.
- Has focused model tests for key relationships and constraints.

**Constraints:** Use Django’s default SQLite database; do not add accounts, authentication, or multi-household support.

## 2. Weekly-round lifecycle service

**Goal:** Implement the domain service that finds or creates the active Monday–Sunday round and carries eligible chores forward from the preceding round.

**Acceptance criteria:**

- A round is identified by its Monday start date.
- Creating a new round preserves the previous round unchanged.
- Eligible chores are copied into the new round as `Pending`.
- A chore removed from a current round is not deleted from history and can be re-added later.
- Has tests for initial-round creation, rollover, and history preservation.

**Constraints:** Keep this as application/domain logic, invoked when the app is used; do not introduce a scheduler or background worker.

## 3. Household setup and pending-list workflow

**Goal:** Provide server-rendered pages for creating the household member list and collecting the initial/current round’s chores.

**Acceptance criteria:**

- Users can create the initial member list before allocation begins.
- A selected member can add a chore to the active round.
- The active round shows its pending chores.
- Members can remove a chore only from the current round and re-add an inactive/removed chore.
- Allocation remains unavailable until every member has added at least one chore.
- Includes form and view tests for the principal validation rules.

**Constraints:** Since there is no authentication, forms explicitly select the acting member.

## 4. Readiness confirmation and allocation preparation

**Goal:** Let every member confirm readiness and calculate the round’s balanced target workloads.

**Acceptance criteria:**

- Each member can confirm “Ready for allocation” once the pending list is valid.
- Allocation is enabled only after every member confirms.
- Target workloads are distributed evenly, differing by at most one task.
- The workload calculation covers uneven task/member counts such as 10/4 and 11/4.
- Has focused tests for readiness gating and workload calculations.

## 5. Two-round chore selection and allocation resolution

**Goal:** Implement the two allocation rounds within one weekly round, including agreement-based conflict resolution and the specified random fallback.

**Acceptance criteria:**

- Members may select up to their target workload plus one preferred chores in the first allocation round.
- An uncontested first-round selection assigns the chore to that member.
- If multiple members select a chore in the first round, those selectors can agree on its assignee.
- If first-round selectors cannot agree, the chore remains unassigned after the first allocation round.
- Only chores unassigned after the first round are available in the second allocation round.
- Members can select unresolved chores again in the second round, including members who did not select that chore in the first round.
- An uncontested second-round selection assigns the chore to that member.
- If multiple second-round selectors cannot agree, random assignment chooses only from those members who selected that chore in the second round.
- The randomly selected second-round selector receives the chore immediately.
- Has service and integration tests for selection limits, first-round unresolved conflicts, second-round additional selectors, agreement, and selector-only random fallback.

**Constraints:** Do not include household members who did not select the unresolved chore in the second round in the random-assignment pool. Keep conflict resolution explicit and server-rendered; do not add notifications or voting.

## 6. Current-week overview and completion tracking

**Goal:** Show the active weekly plan and allow the responsible member to mark assigned chores completed.

**Acceptance criteria:**

- The active-week page shows chores, assignees, and statuses.
- Only the assigned member can be chosen to mark that chore completed.
- A completed chore remains completed for that weekly round.
- Includes view tests for valid and invalid completion actions.

**Constraints:** No user accounts; the responsible member is selected in the form.

## 7. Read-only weekly history

**Goal:** Provide a history page for prior weekly rounds.

**Acceptance criteria:**

- Users can list previous weeks and open a week’s detail page.
- Each historical round displays its chores, assignees, and completion status.
- Historical rounds cannot be edited through the normal UI.
- Includes tests confirming historical data remains visible after rollover.
