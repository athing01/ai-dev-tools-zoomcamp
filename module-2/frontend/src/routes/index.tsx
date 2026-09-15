import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { Plus } from "lucide-react";
import { useState } from "react";

import { BoardError, BoardSkeleton } from "@/components/taskflow/BoardStates";
import { DeleteTaskDialog } from "@/components/taskflow/DeleteTaskDialog";
import { KanbanColumn } from "@/components/taskflow/KanbanColumn";
import { TaskFormDialog } from "@/components/taskflow/TaskFormDialog";
import { groupByStatus, tasksQueryOptions } from "@/lib/tasks/queries";
import { TASK_STATUSES, type Task, type TaskStatus } from "@/lib/tasks/types";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "TaskFlow — Personal Kanban Board" },
      {
        name: "description",
        content:
          "TaskFlow is a clean personal Kanban board: track tasks across To Do, In Progress, and Done.",
      },
      { property: "og:title", content: "TaskFlow — Personal Kanban Board" },
      {
        property: "og:description",
        content:
          "TaskFlow is a clean personal Kanban board: track tasks across To Do, In Progress, and Done.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: BoardPage,
});

type FormState =
  { mode: "closed" } | { mode: "create"; status: TaskStatus } | { mode: "edit"; task: Task };

export function BoardPage() {
  const { data: tasks, isPending, isError, refetch } = useQuery(tasksQueryOptions);
  const [form, setForm] = useState<FormState>({ mode: "closed" });
  const [taskToDelete, setTaskToDelete] = useState<Task | null>(null);

  const grouped = tasks ? groupByStatus(tasks) : null;

  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-sky-100 via-indigo-100 to-cyan-100">
      <div className="pointer-events-none absolute -top-24 -left-16 h-96 w-96 rounded-full bg-white/70 blur-3xl" />
      <div className="pointer-events-none absolute top-40 right-0 h-[28rem] w-[28rem] rounded-full bg-indigo-300/40 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-32 left-1/3 h-96 w-96 rounded-full bg-cyan-300/40 blur-3xl" />

      <div className="relative mx-auto max-w-7xl px-6 py-8">
        <header className="glass-panel flex items-center justify-between rounded-2xl px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-xl bg-gradient-to-br from-brand to-accent text-lg font-bold text-white shadow-md shadow-indigo-500/30">
              T
            </div>
            <div>
              <h1 className="font-display text-xl leading-none font-bold text-ink">TaskFlow</h1>
              <p className="mt-1 text-xs font-medium text-slate-soft">
                Personal board
                {tasks ? ` · ${tasks.length} task${tasks.length === 1 ? "" : "s"}` : ""}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setForm({ mode: "create", status: "todo" })}
            className="inline-flex items-center gap-2 rounded-xl bg-brand px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/30 transition hover:bg-brand-strong"
          >
            <Plus className="size-4" />
            New task
          </button>
        </header>

        {isPending ? (
          <BoardSkeleton />
        ) : isError || !grouped ? (
          <BoardError onRetry={() => refetch()} />
        ) : (
          <main className="mt-6 grid grid-cols-1 gap-5 lg:grid-cols-3">
            {TASK_STATUSES.map((s) => (
              <KanbanColumn
                key={s.value}
                status={s.value}
                tasks={grouped[s.value]}
                onAdd={(status) => setForm({ mode: "create", status })}
                onEdit={(task) => setForm({ mode: "edit", task })}
                onDelete={setTaskToDelete}
              />
            ))}
          </main>
        )}

        <footer className="mt-6 flex items-center justify-between rounded-2xl border border-white/50 bg-white/30 px-5 py-3 text-xs text-slate-soft backdrop-blur-xl">
          <span className="flex items-center gap-2">
            <span className="size-2 rounded-full bg-emerald-400" />
            Mock API connected · data resets on reload
          </span>
          <span>TaskFlow prototype</span>
        </footer>
      </div>

      <TaskFormDialog
        open={form.mode !== "closed"}
        onClose={() => setForm({ mode: "closed" })}
        task={form.mode === "edit" ? form.task : null}
        defaultStatus={form.mode === "create" ? form.status : "todo"}
      />
      <DeleteTaskDialog task={taskToDelete} onClose={() => setTaskToDelete(null)} />
    </div>
  );
}
