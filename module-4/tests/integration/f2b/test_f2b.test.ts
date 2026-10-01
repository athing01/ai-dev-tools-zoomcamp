// Frontend-to-backend integration test.

// This test uses the actual frontend API client (taskService.ts) against a real
// backend connected to PostgreSQL.

// Test mechanism: vitest (Node-side) with the actual frontend API client.
// Reason: The frontend API client is TypeScript code that runs in the browser.
// Using vitest allows us to:
//   - Import the actual TypeScript source (taskService.ts)
//   - Use Node environment for backend integration
//   - Run against a real backend
//   - Exercise the configured frontend -> backend -> PostgreSQL path

// This test requires TEST_DATABASE_URL environment variable to be set, pointing
// to a reachable PostgreSQL instance.

// Run with: cd module-3/frontend && VITE_API_BASE_URL=http://localhost:8000 TEST_DATABASE_URL=... bun run vitest run tests/integration/f2b/test_f2b.test.ts

import { describe, it, expect, beforeAll, afterEach } from "vitest";
import { taskService } from "../../../frontend/src/lib/tasks/taskService";
import { ApiError } from "../../../frontend/src/lib/tasks/types";

describe("Frontend-to-backend integration (f2b)", () => {
  let testTaskIds: number[] = [];

  beforeAll(async () => {
    // Verify backend is reachable by calling the real taskService
    const tasks = await taskService.listTasks();
    expect(Array.isArray(tasks)).toBe(true);
  });

  afterEach(async () => {
    // Clean up all tasks created during this test
    for (const taskId of testTaskIds) {
      try {
        await taskService.deleteTask(taskId);
      } catch (error) {
        // Ignore errors - task may already be deleted or stale
      }
    }
    testTaskIds = [];
  });

  it("lists tasks - can find created task", async () => {
    // Create a task specifically for this test
    const task = await taskService.createTask({
      title: "List Test Task",
      description: "Task created for list verification",
      status: "todo"
    });
    testTaskIds.push(task.id);

    const tasks = await taskService.listTasks();
    // Find the task by its returned ID (primary identity)
    const ourTask = tasks.find(t => t.id === task.id);
    expect(ourTask).toBeDefined();
    expect(ourTask!.id).toBe(task.id);
    expect(ourTask!.title).toBe("List Test Task");
    expect(ourTask!.description).toBe("Task created for list verification");
    expect(ourTask!.status).toBe("todo");
  });



  it("creates a task via frontend API client", async () => {
    const task = await taskService.createTask({
      title: "Frontend Created Task",
      description: "Created via frontend client",
      status: "todo"
    });

    expect(task).not.toBeNull();
    expect(task.id).toBeDefined();
    expect(typeof task.id).toBe("number");
    expect(task.title).toBe("Frontend Created Task");
    expect(task.description).toBe("Created via frontend client");
    expect(task.status).toBe("todo");
    expect(task.created_at).toBeDefined();
    expect(task.updated_at).toBeDefined();

    testTaskIds.push(task.id);
  });

  it("lists tasks - includes multiple created tasks", async () => {
    // Create first task specifically for this test
    const task1 = await taskService.createTask({
      title: "List Test Task 1",
      description: "First task for multiple-item list verification",
      status: "todo"
    });
    testTaskIds.push(task1.id);

    // Create second task specifically for this test
    const task2 = await taskService.createTask({
      title: "List Test Task 2",
      description: "Second task for multiple-item list verification",
      status: "todo"
    });
    testTaskIds.push(task2.id);

    const tasks = await taskService.listTasks();
    // Find each task by their returned IDs (primary identity)
    const ourTask1 = tasks.find(t => t.id === task1.id);
    const ourTask2 = tasks.find(t => t.id === task2.id);

    expect(ourTask1).toBeDefined();
    expect(ourTask1!.id).toBe(task1.id);
    expect(ourTask1!.title).toBe("List Test Task 1");
    expect(ourTask1!.description).toBe("First task for multiple-item list verification");
    expect(ourTask1!.status).toBe("todo");

    expect(ourTask2).toBeDefined();
    expect(ourTask2!.id).toBe(task2.id);
    expect(ourTask2!.title).toBe("List Test Task 2");
    expect(ourTask2!.description).toBe("Second task for multiple-item list verification");
    expect(ourTask2!.status).toBe("todo");
  });

  it("updates a task via frontend API client (partial update)", async () => {
    // Create a task specifically for this test
    const task = await taskService.createTask({
      title: "Update Test Task",
      description: "Task created for update test",
      status: "todo"
    });
    testTaskIds.push(task.id);

    const updated = await taskService.updateTask(task.id, {
      title: "Updated Title",
      status: "in_progress"
    });

    expect(updated).not.toBeNull();
    expect(updated.title).toBe("Updated Title");
    expect(updated.description).toBe("Task created for update test"); // unchanged
    expect(updated.status).toBe("in_progress");
    expect(updated.updated_at).toBeDefined();
  });

  it("changes task status via frontend API client", async () => {
    // Create a task specifically for this test
    const task = await taskService.createTask({
      title: "Status Change Task",
      description: "Task created for status change test",
      status: "todo"
    });
    testTaskIds.push(task.id);

    const updated = await taskService.updateTask(task.id, {
      status: "done"
    });

    expect(updated.status).toBe("done");

    const allTasks = await taskService.listTasks();
    const ourTask = allTasks.find(t => t.id === task.id);
    expect(ourTask).toBeDefined();
    expect(ourTask!.status).toBe("done");
  });

  it("deletes a task via frontend API client", async () => {
    // Create a task specifically for this test
    const task = await taskService.createTask({
      title: "Delete Test Task",
      description: "Task created for delete test",
      status: "todo"
    });
    testTaskIds.push(task.id);

    await taskService.deleteTask(task.id);

    const allTasks = await taskService.listTasks();
    const ourTask = allTasks.find(t => t.id === task.id);
    expect(ourTask).toBeUndefined();
  });

  it("handles missing resources (404) via frontend API client", async () => {
    // Update non-existent task
    await expect(taskService.updateTask(99999, { title: "New Title" }))
      .rejects.toThrow(ApiError);

    try {
      await taskService.updateTask(99999, { title: "New Title" });
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      if (e instanceof ApiError) {
        expect(e.status).toBe(404);
      }
    }

    // Delete non-existent task
    await expect(taskService.deleteTask(99999))
      .rejects.toThrow(ApiError);

    try {
      await taskService.deleteTask(99999);
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      if (e instanceof ApiError) {
        expect(e.status).toBe(404);
      }
    }
  });

  it("verifies timezone-aware UTC timestamps", async () => {
    const task = await taskService.createTask({
      title: "Timestamp Test",
      description: "Testing timestamps",
      status: "todo"
    });
    testTaskIds.push(task.id);

    // Both timestamps should be ISO strings with timezone info
    expect(task.created_at).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$/);
    expect(task.updated_at).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$/);

    // Clean up handled by afterEach
  });

  it("verifies updated_at advances on update", async () => {
    const task = await taskService.createTask({
      title: "Original",
      description: "Desc",
      status: "todo"
    });
    testTaskIds.push(task.id);

    const originalUpdatedAt = task.updated_at;

    // Small delay to ensure timestamp difference
    await new Promise(resolve => setTimeout(resolve, 10));

    const updated = await taskService.updateTask(task.id, { title: "Updated" });
    expect(updated.updated_at).not.toBe(originalUpdatedAt);
    expect(new Date(updated.updated_at).getTime()).toBeGreaterThan(
      new Date(originalUpdatedAt).getTime()
    );

    // Clean up handled by afterEach
  });
});
