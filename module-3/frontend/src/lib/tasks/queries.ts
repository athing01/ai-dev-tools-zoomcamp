import { queryOptions, useMutation, useQueryClient } from "@tanstack/react-query";

import { taskService } from "./taskService";
import type { CreateTaskInput, Task, UpdateTaskInput } from "./types";

export const tasksQueryOptions = queryOptions({
  queryKey: ["tasks"],
  queryFn: () => taskService.listTasks(),
});

export function useCreateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateTaskInput) => taskService.createTask(input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function useUpdateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: UpdateTaskInput }) =>
      taskService.updateTask(id, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function useDeleteTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => taskService.deleteTask(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function groupByStatus(tasks: Task[]) {
  return {
    todo: tasks.filter((t) => t.status === "todo"),
    in_progress: tasks.filter((t) => t.status === "in_progress"),
    done: tasks.filter((t) => t.status === "done"),
  };
}
