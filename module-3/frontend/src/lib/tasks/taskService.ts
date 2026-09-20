import {
  ApiError,
  type CreateTaskInput,
  type Task,
  type TaskService,
  type UpdateTaskInput,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

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
    const response = await fetch(`${API_BASE_URL}/api/tasks`);
    return handleResponse(response) as Promise<Task[]>;
  },

  async createTask(input: CreateTaskInput) {
    const response = await fetch(`${API_BASE_URL}/api/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
    return handleResponse(response) as Promise<Task>;
  },

  async updateTask(id: number, input: UpdateTaskInput) {
    const response = await fetch(`${API_BASE_URL}/api/tasks/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
    return handleResponse(response) as Promise<Task>;
  },

  async deleteTask(id: number) {
    const response = await fetch(`${API_BASE_URL}/api/tasks/${id}`, {
      method: "DELETE",
    });
    await handleResponse(response);
  },
};
