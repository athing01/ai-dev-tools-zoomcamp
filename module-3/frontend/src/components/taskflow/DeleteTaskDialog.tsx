import { toast } from "sonner";

import { useDeleteTask } from "@/lib/tasks/queries";
import type { Task } from "@/lib/tasks/types";
import { Modal } from "./Modal";

interface DeleteTaskDialogProps {
  task: Task | null;
  onClose: () => void;
}

export function DeleteTaskDialog({ task, onClose }: DeleteTaskDialogProps) {
  const deleteTask = useDeleteTask();

  const handleConfirm = async () => {
    if (!task) return;
    try {
      await deleteTask.mutateAsync(task.id);
      toast.success(`Deleted “${task.title}”`);
      onClose();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not delete the task.");
    }
  };

  return (
    <Modal open={Boolean(task)} onClose={onClose} labelledBy="delete-task-title">
      <h2 id="delete-task-title" className="font-display text-lg font-bold text-ink">
        Delete task?
      </h2>
      <p className="mt-2 text-sm leading-relaxed text-slate-soft">
        “<span className="font-semibold text-ink">{task?.title}</span>” will be permanently removed
        from your board. This can't be undone.
      </p>
      <div className="mt-6 flex items-center justify-end gap-2">
        <button
          type="button"
          onClick={onClose}
          disabled={deleteTask.isPending}
          className="rounded-xl px-4 py-2 text-sm font-medium text-slate-soft transition hover:bg-slate-100 disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={handleConfirm}
          disabled={deleteTask.isPending}
          className="rounded-xl bg-rose-500 px-5 py-2 text-sm font-semibold text-white shadow-lg shadow-rose-500/30 transition hover:bg-rose-600 disabled:opacity-60"
        >
          {deleteTask.isPending ? "Deleting…" : "Delete task"}
        </button>
      </div>
    </Modal>
  );
}
