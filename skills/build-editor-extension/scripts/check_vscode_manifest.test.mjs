import { afterAll, describe, expect, test } from "bun:test";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { RULES, check, main } from "./check_vscode_manifest.mjs";

const BASE = {
  name: "todo-owner",
  version: "0.2.0",
  publisher: "acme",
  engines: { vscode: "^1.74.0" },
  categories: ["Linters"],
  main: "./dist/extension.js",
  activationEvents: [],
  capabilities: {
    untrustedWorkspaces: {
      supported: "limited",
      description: "Reading the owner from git runs an executable.",
      restrictedConfigurations: ["todoOwner.gitPath"],
    },
    virtualWorkspaces: { supported: "limited", description: "Needs a local folder." },
  },
  contributes: {
    commands: [
      { command: "todoOwner.addOwner", title: "Add Owner" },
      { command: "todoOwner.showLog", title: "Show Log" },
    ],
    menus: { commandPalette: [{ command: "todoOwner.addOwner", when: "false" }] },
    configuration: {
      title: "TODO Owner",
      properties: {
        "todoOwner.gitPath": { type: "string", scope: "machine-overridable" },
      },
    },
  },
  devDependencies: { "@types/vscode": "1.74.0" },
};
BASE.contributes.configuration.properties["todoOwner.enable"] = { type: "boolean", scope: "resource" };

const SOURCE = `registerCommand("todoOwner.addOwner", f);\nregisterCommand('todoOwner.showLog', g);\n`;
const tmp = mkdtempSync(join(tmpdir(), "vscode-manifest-"));
afterAll(() => rmSync(tmp, { recursive: true, force: true }));
let counter = 0;

function write(manifest, source) {
  const dir = join(tmp, `case${counter++}`);
  mkdirSync(join(dir, "src"), { recursive: true });
  writeFileSync(join(dir, "package.json"), JSON.stringify(manifest));
  writeFileSync(join(dir, "src/extension.ts"), source ?? SOURCE);
  return dir;
}

function run(mutate, { source, built = false, preRelease = false } = {}) {
  const manifest = structuredClone(BASE);
  mutate?.(manifest);
  const dir = write(manifest, source);
  return check(join(dir, "package.json"), { sources: [join(dir, "src")], built, preRelease });
}

const rules = (report) => new Set(report.findings.map((f) => f.rule));

describe("each rule", () => {
  test("base manifest is clean", () => {
    expect(run().lines).toEqual([]);
  });
  const cases = {
    M001: (m) => delete m.publisher,
    M002: (m) => (m.engines.vscode = "*"),
    M003: (m) => (m.name = "Todo Owner"),
    M004: (m) => (m.version = "1.0.0-rc.1"),
    M005: (m) => (m.keywords = Array.from({ length: 31 }, (_, i) => `k${i}`)),
    M006: (m) => (m.icon = "icon.svg"),
    M007: (m) => (m.categories = ["Tools"]),
    M008: (m) => (m.contributes.configuration.properties["todoOwner.enable.fast"] = { type: "boolean" }),
    M009: (m) => (m.contributes.configuration.properties["todoOwner.x"] = { scope: "user" }),
    M010: (m) => (m.contributes.configuration.properties["todoOwner.x"] = { $ref: "#/x" }),
    M011: (m) => delete m.capabilities.untrustedWorkspaces.description,
    M012: (m) => (m.capabilities.untrustedWorkspaces.restrictedConfigurations = ["todoOwner.missing"]),
    M013: (m) => (m.capabilities.virtualWorkspaces = { supported: "limited" }),
    M014: (m) => m.contributes.menus.commandPalette.push({ command: "todoOwner.typo" }),
    M016: (m) => {
      m.engines.vscode = "^1.73.0";
      m.devDependencies["@types/vscode"] = "1.73.1";
    },
    M020: (m) => (m.devDependencies["@types/vscode"] = "^1.138.0"),
    M021: (m) => delete m.capabilities.untrustedWorkspaces,
  };
  for (const [rule, mutate] of Object.entries(cases)) {
    test(`${rule} fires`, () => {
      expect(rules(run(mutate)).has(rule)).toBe(true);
    });
  }
  test("M015 command never registered", () => {
    expect(rules(run(undefined, { source: "registerCommand('x', f)" })).has("M015")).toBe(true);
  });
  test("M016 is satisfied by explicit events", () => {
    const report = run((m) => {
      m.engines.vscode = "^1.73.0";
      m.devDependencies["@types/vscode"] = "1.73.1";
      m.activationEvents = m.contributes.commands.map((c) => `onCommand:${c.command}`);
    });
    expect(rules(report).has("M016")).toBe(false);
  });
  test("M017 star activation is a warning", () => {
    const report = run((m) => (m.activationEvents = ["*"]));
    expect(report.lines).toContain("M017 warning: `*` activates at startup; use a specific event");
    expect(report.errors).toBe(0);
  });
  test("M018 missing bundle", () => {
    expect(rules(run(undefined, { built: true })).has("M018")).toBe(true);
  });
  test("M019 pre-release needs 1.63", () => {
    const report = run(
      (m) => {
        m.engines.vscode = "^1.60.0";
        m.devDependencies["@types/vscode"] = "1.60.0";
      },
      { preRelease: true },
    );
    expect(rules(report).has("M019")).toBe(true);
  });
  test("every rule has a source", () => {
    for (const url of Object.values(RULES)) expect(url.startsWith("https://")).toBe(true);
  });
});

describe("command line", () => {
  const capture = (fn) => {
    const out = [];
    const log = console.log;
    console.log = (text) => out.push(text);
    try {
      return { status: fn(), out: out.join("\n") };
    } finally {
      console.log = log;
    }
  };

  test("exit codes", () => {
    const good = join(write(BASE), "package.json");
    const bad = join(write({ ...BASE, version: "1.0" }), "package.json");
    const broken = join(write(BASE), "broken.json");
    writeFileSync(broken, "{");
    const ok = capture(() => main([good]));
    expect(ok.status).toBe(0);
    expect(ok.out).toContain("0 error(s), 0 warning(s)");
    const fail = capture(() => main([bad]));
    expect(fail.status).toBe(1);
    expect(fail.out).toContain("M004 error");
    expect(main([broken])).toBe(2);
    expect(main([])).toBe(2);
  });

  test("json report", () => {
    const bad = join(write({ ...BASE, version: "1.0" }), "package.json");
    const { status, out } = capture(() => main([bad, "--json"]));
    const report = JSON.parse(out);
    expect(status).toBe(1);
    expect([report.errors, report.warnings]).toEqual([1, 0]);
    expect(report.findings[0].rule).toBe("M004");
    expect(report.findings[0].source).toBe(RULES.M004);
  });

  test("--help exits 0", () => {
    const original = process.stdout.write;
    process.stdout.write = () => true;
    try {
      expect(main(["--help"])).toBe(0);
    } finally {
      process.stdout.write = original;
    }
  });
});
