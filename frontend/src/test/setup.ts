import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// `vitest.config`'s `test.globals` is left off (see vite.config.ts), so
// Testing Library can't auto-detect a global `afterEach` to hook its
// cleanup into — do it explicitly instead.
afterEach(() => {
  cleanup();
});
