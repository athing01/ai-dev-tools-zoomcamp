# Plan: Shared Household Chores Manager

## 1. Goal

Build a small Django web app for managing shared household chores on a weekly cycle.

The MVP focuses on four core capabilities:

1. Weekly household chore list management
2. Fair task allocation
3. Task assignment and completion tracking
4. Weekly history

The MVP uses one household/group only and does not require user login or authentication.

## 2. Scope

### Members

- There is one household/group.
- One person sets up the complete member list before the system is used.
- Each member is identified by their name.
- Members do not need to create accounts or log in.

### Weekly round

- The system works in weekly rounds: Monday through Sunday.
- A new weekly round starts automatically.
- A new round is based on the previous week's task list.
- Members can add new tasks or bring previously inactive/removed tasks back into the current pending list.
- Tasks from previous weeks are kept as history and are not edited retroactively.

### Initial / pending task list

For the first task list:

- Every member can add household chores.
- The system collects all proposed chores into one list.
- The system does not allow allocation to start until every member has added at least one task.
- Once the list is complete, the full list is shown to everyone.
- Every member must confirm **Ready for allocation**.
- Allocation starts only after all members have confirmed.

For later weekly rounds:

- The previous round's tasks are carried into the new round as pending tasks.
- Members can add new tasks.
- Members can remove a task from the current round without deleting its historical record.
- Previously inactive tasks can be brought back into the current pending list.
- Task cleanup/lifecycle should preserve history.

## 3. Allocation rules

### Workload calculation

The system calculates each member's target number of tasks automatically.

- The target workload is based on the total number of tasks and number of members.
- Workloads should be distributed as evenly as possible.
- The number of assigned tasks between any two members should differ by no more than 1.

Examples:

- 10 tasks / 4 members -> 3, 3, 2, 2
- 11 tasks / 4 members -> 3, 3, 3, 2

### Task selection

- Each member may select up to **target workload + 1** tasks.
- The extra choice gives members some flexibility when several people want the same task.

### Conflict resolution

When multiple members select the same task:

1. First allocation round:
   - Members may agree among themselves who should take the task.
   - If they cannot agree, the task remains unassigned for this round.

2. Second allocation round:
   - The unassigned task is considered again.
   - If members still cannot agree, the system randomly selects one of the eligible members.
   - The selected member receives the task immediately; no additional confirmation is required.

The allocation process continues until all tasks are assigned.

## 4. Task status

Each assigned task has two statuses:

- `Not completed`
- `Completed`

The member responsible for a task marks it **Completed** when the chore is finished.

At the start of the next weekly round:

- Recurring household tasks return to `Pending` automatically.
- The previous week's assignment/status remains available in history.

## 5. Weekly history

The system keeps each weekly round as separate historical data.

Members can view previous weeks and see:

- The tasks in that week
- Who was responsible for each task
- Whether each task was completed

Historical rounds should be read-only from the normal user workflow.

## 6. Task lifecycle

A task can move through this general lifecycle:

`Pending -> Assigned -> Completed`

For the next weekly round, routine tasks return to:

`Completed -> Pending`

A task that is not used for a period may become inactive.

Planned cleanup rule:

- If a task is still used again within one month, keep it.
- If it has not been used for more than one month, it may be considered inactive.

For the MVP, inactivity should be handled conservatively and should not delete historical records. Automatic permanent deletion is out of scope.

## 7. Main user flow

### First setup

1. Set up the household member list.
2. Each member adds at least one chore.
3. System shows the complete initial task list.
4. Every member clicks **Ready for allocation**.
5. System calculates target workload for each member.
6. Members select tasks (up to target + 1).
7. Resolve duplicate selections by agreement.
8. Leave unresolved tasks unassigned for the first allocation round.
9. Reconsider unresolved tasks in the second allocation round.
10. If still unresolved, randomly assign them.
11. Show each member's assigned tasks.

### During the week

1. Members view their assigned tasks.
2. A responsible member marks a task **Completed** when finished.
3. Members can view the current weekly overview.

### New week

1. A new weekly round starts automatically.
2. Previous tasks are carried into the new round as pending tasks.
3. Members add/remove/re-add tasks as needed.
4. Every member confirms **Ready for allocation**.
5. The allocation process runs again.
6. The new round becomes the active weekly plan.
7. Previous rounds remain available in history.

## 8. MVP non-goals / future features

These are intentionally outside the MVP:

- Multiple households/groups
- User accounts and authentication
- Invitations
- Voting to approve newly proposed chores
- Notifications
- Mobile app
- Advanced analytics, scores, rankings, or gamification
- Automatic permanent deletion of old tasks
- Complex recurring schedules beyond the weekly round

A future version may add a voting workflow for newly proposed chores after the initial list has been established.

## 9. Technical direction

- Framework: Django
- Use a simple server-rendered web application for the MVP.
- Keep the data model centered around:
  - Household members
  - Weekly rounds
  - Tasks
  - Per-round task assignments/status
  - Allocation selections/conflicts
- Preserve weekly rounds as separate records so historical data is not overwritten.

## 10. Success criteria

The MVP is successful when a household can:

1. Set up its members.
2. Collect the initial chore list collaboratively.
3. Confirm that everyone is ready.
4. Automatically calculate a balanced workload.
5. Let members choose preferred chores.
6. Resolve conflicts using agreement first and random fallback when needed.
7. Track completion during the week.
8. Start the next week automatically with the previous task set.
9. Review previous weekly assignments and completion status.
