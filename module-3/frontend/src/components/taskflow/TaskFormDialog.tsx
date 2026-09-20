import { useEffect, useState } from "react";
import { toast } from "sonner";

import { useCreateTask, useUpdateTask } from "@/lib/tasks/queries";
import { TASK_STATUSES, type Task, type TaskStatus } from "@/lib/tasks/types";
import { Modal } from "./Modal";

interface TaskFormDialogProps {
  open: boolean;
  onClose: () => void;
  /** When set, the dialog edits this task; otherwise it creates a new one. */
  task?: Task | null;
  defaultStatus?: TaskStatus;
}

export function TaskFormDialog({
  open,
  onClose,
  task,
  defaultStatus = "todo",
}: TaskFormDialogProps) {
  const isEditing = Boolean(task);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<TaskStatus>(defaultStatus);
  const [titleError, setTitleError] = useState<string | null>(null);

  const createTask = useCreateTask();
  const updateTask = useUpdateTask();
  const isSaving = createTask.isPending || updateTask.isPending;

  useEffect(() => {
    if (open) {
      setTitle(task?.title ?? "");
      setDescription(task?.description ?? "");
      setStatus(task?.status ?? defaultStatus);
      setTitleError(null);
    }
  }, [open, task, defaultStatus]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = title.trim();
    if (!trimmed) {
      setTitleError("Title must contain at least one non-whitespace character.");
      return;
    }
    try {
      if (isEditing && task) {
        await updateTask.mutateAsync({
          id: task.id,
          input: { title: trimmed, description },
        });
        toast.success("Task updated");
      } else {
        await createTask.mutateAsync({ title: trimmed, description, status });
        toast.success("Task created");
      }
      onClose();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Something went wrong.");
    }
  };

  return (
    <Modal open={open} onClose={onClose} labelledBy="task-form-title">
      <h2 id="task-form-title" className="font-display text-lg font-bold text-ink">
        {isEditing ? "Edit task" : "New task"}
      </h2>
      <p className="mt-1 text-xs font-medium text-slate-soft">
        {isEditing ? "Update the title or description." : "Add it to your board."}
      </p>

      <form onSubmit={handleSubmit} className="mt-5 space-y-4">
        <div>
          <label htmlFor="task-title" className="mb-1 block text-xs font-semibold text-ink">
            Title <span className="text-brand">*</span>
          </label>
          <input
            id="task-title"
            type="text"
            value={title}
            onChange={(e) => {
              setTitle(e.target.value);
              if (titleError) setTitleError(null);
            }}
            placeholder="e.g. Review the Q2 roadmap"
            autoFocus
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-ink outline-none transition placeholder:text-slate-400 focus:border-brand focus:ring-2 focus:ring-brand/20"
          />
          {titleError && <p className="mt-1 text-xs font-medium text-rose-500">{titleError}</p>}
        </div>

        <div>
          <label
            htmlFor="task-description"
            className="mb-1 block text-xs font-semibold text-ink"
          >
            Description <span className="font-normal text-slate-soft">(optional)</span>
          </label>
          <textarea
            id="task-description"
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Optional notes, links, or context."
            className="w-full resize-none rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm leading-relaxed text-ink outline-none transition placeholder:text-slate-400 focus:border-brand focus:ring-2 focus:ring-brand/20"
          />
        </div>

        {!isEditing && (
          <div>
            <span className="mb-1 block text-xs font-semibold text-ink">Initial status</span>
            <div className="flex gap-2">
              {TASK_STATUSES.map((s) => (
                <button
                  key={s.value}
                  type="button"
                  onClick={() => setStatus(s.value)}
                  aria-pressed={status === s.value}
                  className={`flex-1 rounded-xl border px-3 py-2 text-xs font-semibold transition ${
                    status === s.value
                      ? "border-brand bg-brand/10 text-brand"
                      : "border-slate-200 bg-white text-slate-soft hover:border-slate-300"
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="flex items-center justify-end gap-2 pt-1">
          <button
            type="button"
            onClick={onClose}
            disabled={isSaving}
            className="rounded-xl px-4 py-2 text-sm font-medium text-slate-soft transition hover:bg-slate-100 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSaving}
            className="rounded-xl bg-brand px-5 py-2 text-sm font-semibold text-white shadow-lg shadow-indigo-500/30 transition hover:bg-brand-strong disabled:opacity-60"
          >
            {isSaving ? "Saving…" : isEditing ? "Save changes" : "Create task"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
