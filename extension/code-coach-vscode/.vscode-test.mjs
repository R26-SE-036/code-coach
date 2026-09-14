import { defineConfig } from "@vscode/test-cli";

export default defineConfig({
  files: "out/test/**/*.test.js",
  // The build already in .vscode-test, so a test run does not start with a
  // download. Raise it deliberately when testing against a newer VS Code.
  version: "1.116.0",
  // Other installed extensions have no business in these tests, and one of them
  // opening its own prompts would be read as the extension under test's.
  launchArgs: ["--disable-extensions"],
  mocha: {
    timeout: 60000,
  },
  download: {
    timeout: 120000,
  },
});
