import {
  ApiError,
  type CreateTaskInput,
  type Task,
  type TaskService,
  type UpdateTaskInput,
} from "./types";

/**
 * In-memory mock of the TaskFlow REST API.
 *
 * Mimics real backend behavior: network latency, server-side validation,
 * ISO timestamps, and 404s. To demo the API error state, temporarily set
 * FAILURE_RATE to a value between 0 and 1.
 */
const FAILURE_RATE = 0;
const MIN_LATENCY_MS = 250;
const MAX_LATENCY_MS = 550;

function daysAgo(n: number, hour = 10): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  d.setHours(hour, 15, 0, 0);
  return d.toISOString();
}

let store: Task[] = [
  {
    id: "task_001",
    title: "Design onboarding flow",
    description:
      "Outline the first-run checklist, empty states, and the welcome card copy.",
    status: "todo",
    created_at: daysAgo(6),
    updated_at: daysAgo(6),
  },
  {
    id: "task_002",
    title: "Write API service layer",
    description:
      "Wrap all task calls in a mock service so the UI never touches data directly.",
    status: "todo",
    created_at: daysAgo(5),
    updated_at: daysAgo(5),
  },
  {
    id: "task_003",
    title: "Build drag-and-drop columns",
    description: "Wire status moves with a smooth ghost preview and drop indicators.",
    status: "in_progress",
    created_at: daysAgo(4),
    updated_at: daysAgo(1, 16),
  },
  {
    id: "task_004",
    title: "Set up Tailwind v4 tokens",
    description: "Add brand, accent, ink and surface tokens plus display font.",
    status: "done",
    created_at: daysAgo(8),
    updated_at: daysAgo(3),
  },
  {
    id: "task_005",
    title: "Draft task data model",
    description: "id, title, description, status, created_at, updated_at.",
    status: "done",
    created_at: daysAgo(9),
    updated_at: daysAgo(4),
  },
];

let idCounter = 6;

function simulateNetwork(): Promise<void> {
  const latency = MIN_LATENCY_MS + Math.random() * (MAX_LATENCY_MS - MIN_LATENCY_MS);
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (Math.random() < FAILURE_RATE) {
        reject(new ApiError("The task service is unavailable. Please try again.", 503));
      } else {
        resolve();
      }
    }, latency);
  });
}

function requireNonEmptyTitle(title: string): string {
  const trimmed = title.trim();
  if (!trimmed) {
    throw new ApiError("Title must contain at least one non-whitespace character.", 422);
  }
  return trimmed;
}

export const mockTaskService: TaskService = {
  async listTasks() {
    await simulateNetwork();
    return store.map((t) => ({ ...t }));
  },

  async createTask(input: CreateTaskInput) {
    await simulateNetwork();
    const now = new Date().toISOString();
    const task: Task = {
      id: `task_${String(idCounter++).padStart(3, "0")}`,
      title: requireNonEmptyTitle(input.title),
      description: input.description?.trim() ?? "",
      status: input.status ?? "todo",
      created_at: now,
      updated_at: now,
    };
    store = [task, ...store];
    return { ...task };
  },

  async updateTask(id: string, input: UpdateTaskInput) {
    await simulateNetwork();
    const existing = store.find((t) => t.id === id);
    if (!existing) throw new ApiError("Task not found.", 404);

    const updated: Task = {
      ...existing,
      ...(input.title !== undefined ? { title: requireNonEmptyTitle(input.title) } : {}),
      ...(input.description !== undefined ? { description: input.description.trim() } : {}),
      ...(input.status !== undefined ? { status: input.status } : {}),
      updated_at: new Date().toISOString(),
    };
    store = store.map((t) => (t.id === id ? updated : t));
    return { ...updated };
  },

  async deleteTask(id: string) {
    await simulateNetwork();
    if (!store.some((t) => t.id === id)) throw new ApiError("Task not found.", 404);
    store = store.filter((t) => t.id !== id);
  },
};

/** Swap point: replace with a REST client implementing TaskService. */
export const taskService: TaskService = mockTaskService;
