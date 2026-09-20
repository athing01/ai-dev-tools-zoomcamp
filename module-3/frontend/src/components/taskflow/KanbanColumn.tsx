import { Plus } from "lucide-react";

import type { Task, TaskStatus } from "@/lib/tasks/types";
import { TaskCard } from "./TaskCard";

const COLUMN_META: Record<TaskStatus, { label: string; dot: string; emptyText: string }> = {
  todo: {
    label: "To Do",
    dot: "bg-sky-500",
    emptyText: "Nothing planned yet. Add a task to get started.",
  },
  in_progress: {
    label: "In Progress",
    dot: "bg-amber-400",
    emptyText: "Nothing in flight. Move a task here when you start it.",
  },
  done: {
    label: "Done",
    dot: "bg-emerald-500",
    emptyText: "No finished tasks yet. Completed work lands here.",
  },
};

interface KanbanColumnProps {
  status: TaskStatus;
  tasks: Task[];
  onAdd: (status: TaskStatus) => void;
  onEdit: (task: Task) => void;
  onDelete: (task: Task) => void;
}

export function KanbanColumn({ status, tasks, onAdd, onEdit, onDelete }: KanbanColumnProps) {
  const meta = COLUMN_META[status];

  return (
    <section
      aria-label={meta.label}
      className="glass-panel flex flex-col rounded-2xl p-4"
    >
      <div className="mb-4 flex items-center justify-between px-1">
        <div className="flex items-center gap-2">
          <span className={`size-2.5 rounded-full ${meta.dot}`} />
          <h2 className="font-display text-sm font-semibold text-ink">{meta.label}</h2>
          <span className="rounded-full bg-white/60 px-2 py-0.5 text-xs font-semibold text-slate-soft">
            {tasks.length}
          </span>
        </div>
        <button
          type="button"
          onClick={() => onAdd(status)}
          aria-label={`Add task to ${meta.label}`}
          className="grid size-7 place-items-center rounded-lg bg-white/50 text-slate-soft transition hover:bg-white/80 hover:text-ink"
        >
          <Plus className="size-4" />
        </button>
      </div>

      {tasks.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center rounded-xl border border-dashed border-slate-300/70 px-4 py-10 text-center">
          <p className="text-xs font-medium text-slate-soft">{meta.emptyText}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {tasks.map((task) => (
            <TaskCard key={task.id} task={task} onEdit={onEdit} onDelete={onDelete} />
          ))}
        </div>
      )}
    </section>
  );
}
