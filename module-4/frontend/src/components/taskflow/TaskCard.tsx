import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { ArrowRightLeft, Check, Pencil, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { useUpdateTask } from "@/lib/tasks/queries";
import { TASK_STATUSES, type Task, type TaskStatus } from "@/lib/tasks/types";

const STATUS_STYLES: Record<TaskStatus, { dot: string; badge: string }> = {
  todo: { dot: "bg-sky-500", badge: "bg-sky-50 text-sky-600" },
  in_progress: { dot: "bg-amber-400", badge: "bg-amber-50 text-amber-600" },
  done: { dot: "bg-emerald-500", badge: "bg-emerald-50 text-emerald-600" },
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "2-digit" });
}

interface TaskCardProps {
  task: Task;
  onEdit: (task: Task) => void;
  onDelete: (task: Task) => void;
}

export function TaskCard({ task, onEdit, onDelete }: TaskCardProps) {
  const updateTask = useUpdateTask();
  const styles = STATUS_STYLES[task.status];
  const isDone = task.status === "done";

  const handleMove = async (status: TaskStatus) => {
    if (status === task.status) return;
    try {
      await updateTask.mutateAsync({ id: task.id, input: { status } });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not move the task.");
    }
  };

  return (
    <article className="glass-card group rounded-xl p-4">
      {task.status === "in_progress" && (
        <div className="mb-2 flex items-center gap-1.5">
          <span className="size-1.5 animate-pulse-soft rounded-full bg-amber-400" />
          <span className="text-[11px] font-semibold tracking-wide text-amber-500 uppercase">
            In progress
          </span>
        </div>
      )}
      <div className="flex items-start justify-between gap-2">
        <h3
          className={`text-sm font-semibold text-ink ${
            isDone ? "line-through decoration-slate-300" : ""
          }`}
        >
          {task.title}
        </h3>
        <div className="flex shrink-0 gap-1 opacity-0 transition group-hover:opacity-100">
          <button
            type="button"
            onClick={() => onEdit(task)}
            aria-label={`Edit ${task.title}`}
            className="grid size-7 place-items-center rounded-lg bg-white/70 text-slate-soft transition hover:text-ink"
          >
            <Pencil className="size-3.5" />
          </button>
          <button
            type="button"
            onClick={() => onDelete(task)}
            aria-label={`Delete ${task.title}`}
            className="grid size-7 place-items-center rounded-lg bg-rose-50 text-rose-500 transition hover:bg-rose-100"
          >
            <Trash2 className="size-3.5" />
          </button>
        </div>
      </div>

      {task.description && (
        <p className="mt-2 text-xs leading-relaxed text-slate-soft">{task.description}</p>
      )}

      <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-3">
        <span className="text-[11px] font-medium text-slate-soft">
          {isDone ? "Completed" : task.updated_at !== task.created_at ? "Updated" : "Created"}{" "}
          {formatDate(isDone ? task.updated_at : task.updated_at)}
        </span>

        <DropdownMenu.Root>
          <DropdownMenu.Trigger asChild>
            <button
              type="button"
              aria-label={`Change status of ${task.title}`}
              className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold transition hover:brightness-95 ${styles.badge}`}
            >
              <ArrowRightLeft className="size-3" />
              {TASK_STATUSES.find((s) => s.value === task.status)?.label}
            </button>
          </DropdownMenu.Trigger>
          <DropdownMenu.Portal>
            <DropdownMenu.Content
              align="end"
              sideOffset={6}
              className="z-50 min-w-40 rounded-xl border border-white/60 bg-white/95 p-1.5 shadow-xl shadow-indigo-500/10 backdrop-blur-xl"
            >
              {TASK_STATUSES.map((s) => (
                <DropdownMenu.Item
                  key={s.value}
                  onSelect={() => handleMove(s.value)}
                  className="flex cursor-pointer items-center justify-between gap-2 rounded-lg px-2.5 py-2 text-xs font-medium text-ink outline-none data-[highlighted]:bg-slate-100"
                >
                  <span className="flex items-center gap-2">
                    <span className={`size-2 rounded-full ${STATUS_STYLES[s.value].dot}`} />
                    {s.label}
                  </span>
                  {s.value === task.status && <Check className="size-3.5 text-brand" />}
                </DropdownMenu.Item>
              ))}
            </DropdownMenu.Content>
          </DropdownMenu.Portal>
        </DropdownMenu.Root>
      </div>
    </article>
  );
}
