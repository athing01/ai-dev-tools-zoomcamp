import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  root: "..",
  server: {
    fs: {
      allow: ["tests/integration/f2b"],
    },
  },
  test: {
    environment: "node",
    globals: true,
    include: ["tests/integration/f2b/test_f2b.test.ts"],
  },
});
