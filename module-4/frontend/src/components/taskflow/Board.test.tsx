import { describe, it, expect, vi, beforeEach, type Mock } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BoardPage } from "../../routes/index";
import { taskService } from "../../lib/tasks/taskService";

vi.mock("../../lib/tasks/taskService", () => ({
  taskService: {
    listTasks: vi.fn(),
    createTask: vi.fn(),
    updateTask: vi.fn(),
    deleteTask: vi.fn(),
  },
}));

vi.mock("@radix-ui/react-dropdown-menu", async () => {
  const React = await import("react");

  return {
    Root: ({ children }: { children: React.ReactNode }) => <>{children}</>,
    Trigger: ({ children }: { children: React.ReactNode }) => <>{children}</>,
    Portal: ({ children }: { children: React.ReactNode }) => <>{children}</>,
    Content: ({ children }: { children: React.ReactNode }) => <div role="menu">{children}</div>,
    Item: ({ children, onSelect }: { children: React.ReactNode; onSelect?: () => void }) => (
      <div role="menuitem" tabIndex={0} onClick={onSelect}>
        {children}
      </div>
    ),
  };
});

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const renderBoard = (client: QueryClient) => {
  return render(
    <QueryClientProvider client={client}>
      <BoardPage />
    </QueryClientProvider>,
  );
};

describe("BoardPage", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = createTestQueryClient();
    vi.clearAllMocks();
  });

  it("shows loading state initially", async () => {
    (taskService.listTasks as Mock).mockReturnValue(new Promise(() => {}));
    renderBoard(queryClient);
    expect(screen.getByLabelText(/Loading tasks/i)).toBeInTheDocument();
  });

  it("renders tasks after loading", async () => {
    const mockTasks = [
      {
        id: 1,
        title: "Task 1",
        description: "Desc 1",
        status: "todo",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: 2,
        title: "Task 2",
        description: "Desc 2",
        status: "in_progress",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ];
    (taskService.listTasks as Mock).mockResolvedValue(mockTasks);

    renderBoard(queryClient);

    await waitFor(() => {
      expect(screen.getByText("Task 1")).toBeInTheDocument();
      expect(screen.getByText("Task 2")).toBeInTheDocument();
    });
  });

  it("shows error state when API fails", async () => {
    (taskService.listTasks as Mock).mockRejectedValue(new Error("API Error"));

    renderBoard(queryClient);

    await waitFor(() => {
      expect(screen.getByText(/The task service didn't respond/i)).toBeInTheDocument();
    });
  });

  it("opens create task dialog when New task is clicked", async () => {
    (taskService.listTasks as Mock).mockResolvedValue([]);
    renderBoard(queryClient);

    const addButton = screen.getByRole("button", { name: /New task/i });
    fireEvent.click(addButton);

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
  });

  it("creates a task successfully", async () => {
    (taskService.listTasks as Mock).mockResolvedValue([]);
    (taskService.createTask as Mock).mockResolvedValue({
      id: 101,
      title: "New Task",
      description: "Desc",
      status: "todo",
      created_at: "",
      updated_at: "",
    });

    renderBoard(queryClient);

    fireEvent.click(screen.getByRole("button", { name: /New task/i }));

    const titleInput = screen.getByRole("textbox", { name: /title/i });
    fireEvent.change(titleInput, { target: { value: "New Task" } });

    const submitButton = screen.getByRole("button", { name: /Create task/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(taskService.createTask).toHaveBeenCalledWith({
        title: "New Task",
        description: "",
        status: "todo",
      });
    });
  });

  it("edits a task successfully", async () => {
    const mockTasks = [
      {
        id: 1,
        title: "Old Title",
        description: "Desc",
        status: "todo",
        created_at: "",
        updated_at: "",
      },
    ];
    (taskService.listTasks as Mock).mockResolvedValue(mockTasks);
    (taskService.updateTask as Mock).mockResolvedValue({ ...mockTasks[0], title: "New Title" });

    renderBoard(queryClient);

    await waitFor(() => screen.getByText("Old Title"));

    const editButton = screen.getByRole("button", {
      name: new RegExp(`Edit ${mockTasks[0].title}`, "i"),
    });
    fireEvent.click(editButton);

    const titleInput = screen.getByRole("textbox", { name: /title/i });
    fireEvent.change(titleInput, { target: { value: "New Title" } });

    const saveButton = screen.getByRole("button", { name: /Save changes/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(taskService.updateTask).toHaveBeenCalledWith(1, {
        title: "New Title",
        description: "Desc",
      });
    });
  });

  it("deletes a task successfully", async () => {
    const mockTasks = [
      {
        id: 1,
        title: "Task to Delete",
        description: "Desc",
        status: "todo",
        created_at: "",
        updated_at: "",
      },
    ];
    (taskService.listTasks as Mock).mockResolvedValue(mockTasks);
    (taskService.deleteTask as Mock).mockResolvedValue(undefined);

    renderBoard(queryClient);

    await waitFor(() => screen.getByText("Task to Delete"));

    const deleteButton = screen.getByRole("button", {
      name: new RegExp(`Delete ${mockTasks[0].title}`, "i"),
    });
    fireEvent.click(deleteButton);

    // The confirmation button is the only one with "Delete task" text exactly in the dialog
    const confirmButton = screen.getByRole("button", { name: "Delete task" });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(taskService.deleteTask).toHaveBeenCalledWith(1);
    });
  });

  it("handles task status changes", async () => {
    const mockTasks = [
      {
        id: 1,
        title: "Task 1",
        description: "Desc",
        status: "todo",
        created_at: "",
        updated_at: "",
      },
    ];
    (taskService.listTasks as Mock).mockResolvedValue(mockTasks);
    (taskService.updateTask as Mock).mockResolvedValue({ ...mockTasks[0], status: "in_progress" });

    renderBoard(queryClient);

    await waitFor(() => screen.getByText("Task 1"));

    const moveButton = screen.getByRole("button", {
      name: new RegExp(`Change status of ${mockTasks[0].title}`, "i"),
    });
    fireEvent.pointerDown(moveButton, { button: 0, ctrlKey: false });

    const statusItem = await screen.findByRole("menuitem", { name: /In Progress/i });
    fireEvent.click(statusItem);

    await waitFor(() => {
      expect(taskService.updateTask).toHaveBeenCalledWith(1, { status: "in_progress" });
    });
  });
});
