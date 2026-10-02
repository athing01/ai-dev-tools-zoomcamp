import {
  ApiError,
  type CreateTaskInput,
  type Task,
  type TaskService,
  type UpdateTaskInput,
} from "./types";

const CONFIGURED_API_BASE_URL = import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, "");

function resolveApiBaseUrl(): string {
  if (CONFIGURED_API_BASE_URL) {
    return CONFIGURED_API_BASE_URL;
  }

  if (typeof window === "undefined") {
    return "http://localhost:8000";
  }

  const { hostname } = window.location;

  if (hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1") {
    return "http://localhost:8000";
  }

  if (hostname.startsWith("dev-app.")) {
    return `https://dev-api.${hostname.slice("dev-app.".length)}`;
  }

  if (hostname.startsWith("app.")) {
    return `https://api.${hostname.slice("app.".length)}`;
  }

  throw new Error(
    `Unable to derive API hostname from frontend hostname: ${hostname}. ` +
      "Set VITE_API_BASE_URL for this environment.",
  );
}

async function handleResponse(response: Response) {
  if (response.ok) {
    if (response.status === 204) return null;
    return response.json();
  }

  let message = "An unexpected error occurred.";
  try {
    const errorData = await response.json();
    message = errorData.message || message;
  } catch {
    // Response was not JSON
  }

  throw new ApiError(message, response.status);
}

export const taskService: TaskService = {
  async listTasks() {
    const response = await fetch(`${resolveApiBaseUrl()}/api/tasks`);
    return handleResponse(response) as Promise<Task[]>;
  },

  async createTask(input: CreateTaskInput) {
    const response = await fetch(`${resolveApiBaseUrl()}/api/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
    return handleResponse(response) as Promise<Task>;
  },

  async updateTask(id: number, input: UpdateTaskInput) {
    const response = await fetch(`${resolveApiBaseUrl()}/api/tasks/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
    return handleResponse(response) as Promise<Task>;
  },

  async deleteTask(id: number) {
    const response = await fetch(`${resolveApiBaseUrl()}/api/tasks/${id}`, {
      method: "DELETE",
    });
    await handleResponse(response);
  },
};
