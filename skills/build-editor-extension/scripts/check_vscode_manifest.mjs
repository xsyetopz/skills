#!/usr/bin/env bun
// Check a VS Code extension package.json against documented manifest rules.
// Exit status: 0 no errors, 1 at least one error, 2 unreadable input.

import { existsSync, readdirSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { parseArgs } from "node:util";

const DOCS = "https://code.visualstudio.com/api";
const FIELDS = `${DOCS}/references/extension-manifest#fields`;
const PRERELEASE = `${DOCS}/working-with-extensions/publishing-extension#prerelease-extensions`;
const CONFIG = `${DOCS}/references/contribution-points#contributes.configuration`;
const TRUST = `${DOCS}/extension-guides/workspace-trust#static-declarations`;
export const RULES = {
  M001: FIELDS,
  M002: FIELDS,
  M003: FIELDS,
  M004: PRERELEASE,
  M005: FIELDS,
  M006: `${DOCS}/working-with-extensions/publishing-extension#publishing-extensions`,
  M007: FIELDS,
  M008: CONFIG,
  M009: CONFIG,
  M010: CONFIG,
  M011: TRUST,
  M012: TRUST,
  M013: `${DOCS}/extension-guides/virtual-workspaces`,
  M014: "https://github.com/microsoft/vscode/blob/main/src/vs/workbench/services/actions/common/menusExtensionPoint.ts",
  M015: `${DOCS}/extension-guides/command#registering-a-command`,
  M016: `${DOCS}/references/activation-events#onCommand`,
  M017: `${DOCS}/references/activation-events#Start-up`,
  M018: FIELDS,
  M019: PRERELEASE,
  M020: "https://github.com/microsoft/vscode-vsce/blob/main/src/validation.ts",
  M021: `${DOCS}/extension-guides/workspace-trust#what-if-i-dont-make-changes-to-my-extension`,
};

const CATEGORIES = new Set([
  "Programming Languages", "Snippets", "Linters", "Themes", "Debuggers",
  "Formatters", "Keymaps", "SCM Providers", "Other", "Extension Packs",
  "Language Packs", "Data Science", "Machine Learning", "Visualization",
  "Notebooks", "Education", "Testing",
]);
const SCOPES = new Set([
  "application", "machine", "machine-overridable", "window", "resource",
  "language-overridable",
]);
const VERSION = /^\d+\.\d+\.\d+$/;
const ENGINE = /^[\^~>=]*\s*(\d+)\.(\d+)\.(\d+|x)/;
const SOURCE = /\.(ts|js|mts|cts|mjs|cjs)$/;

const HELP = `Usage: check_vscode_manifest.mjs [--src DIR]... [--built] [--pre-release]
                               [--json] PACKAGE_JSON

Check a VS Code package.json against documented manifest rules.

Options:
  --src DIR      source directory to search for registerCommand (M015); repeatable
  --built        check that main/browser files exist (M018)
  --pre-release  apply pre-release rules (M019: engines.vscode >= 1.63)
  --json         print a JSON report
  -h, --help     show this help

Exit status:
  0  no errors (warnings alone do not fail)
  1  at least one error
  2  unreadable input: PACKAGE_JSON is missing or not a JSON object

Output: one "<RULE> <error|warning>: <message>" line per finding, then
"N error(s), N warning(s)". --json prints {"findings": [{rule, level,
message, source}], "errors": N, "warnings": N}; source is the rule's
documentation URL.

Examples:
  bun scripts/check_vscode_manifest.mjs package.json --src src
  bun scripts/check_vscode_manifest.mjs package.json --src src --built --pre-release
  bun scripts/check_vscode_manifest.mjs package.json --json \\
    | jq '.findings[] | select(.level == "error")'
`;

class Report {
  findings = [];
  errors = 0;
  error(rule, message) {
    this.errors += 1;
    this.add(rule, "error", message);
  }
  warn(rule, message) {
    this.add(rule, "warning", message);
  }
  add(rule, level, message) {
    this.findings.push({ rule, level, message, source: RULES[rule] });
  }
  get lines() {
    return this.findings.map((f) => `${f.rule} ${f.level}: ${f.message}`);
  }
}

const isObject = (value) =>
  typeof value === "object" && value !== null && !Array.isArray(value);

function engineFloor(spec) {
  const match = ENGINE.exec(String(spec ?? "").trim());
  return match ? [Number(match[1]), Number(match[2])] : null;
}

const below = (a, b) => a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]);

function checkIdentity(m, r) {
  for (const field of ["name", "version", "publisher"]) {
    if (typeof m[field] !== "string" || !m[field]) {
      r.error("M001", `missing required field \`${field}\``);
    }
  }
  const vscode = isObject(m.engines) ? m.engines.vscode : undefined;
  if (typeof vscode !== "string") {
    r.error("M001", "missing required field `engines.vscode`");
  } else if (vscode.trim() === "*") {
    r.error("M002", "`engines.vscode` cannot be `*`");
  }
  const { name, version, icon } = m;
  if (typeof name === "string" && (name !== name.toLowerCase() || name.includes(" "))) {
    r.error("M003", `name \`${name}\` must be lowercase without spaces`);
  }
  if (typeof version === "string" && !VERSION.test(version)) {
    r.error(
      "M004",
      `version \`${version}\`: Marketplace accepts major.minor.patch only; use --pre-release instead of a semver tag`,
    );
  }
  const keywords = m.keywords ?? [];
  if (Array.isArray(keywords) && keywords.length > 30) {
    r.error("M005", `${keywords.length} keywords; the limit is 30`);
  }
  if (typeof icon === "string" && icon.toLowerCase().endsWith(".svg")) {
    r.error("M006", `icon \`${icon}\` is an SVG; use a PNG`);
  }
  for (const category of m.categories ?? []) {
    if (!CATEGORIES.has(category)) {
      r.error("M007", `category \`${category}\` is not an allowed value`);
    }
  }
}

function settingsOf(contributes) {
  const config = contributes.configuration ?? [];
  const found = {};
  for (const block of Array.isArray(config) ? config : [config]) {
    if (isObject(block)) Object.assign(found, block.properties ?? {});
  }
  return found;
}

function checkConfiguration(contributes, r) {
  const settings = settingsOf(contributes);
  const ids = Object.keys(settings).sort();
  for (const a of ids) {
    for (const b of ids) {
      if (a !== b && b.startsWith(`${a}.`)) {
        r.error("M008", `setting \`${a}\` is a full prefix of \`${b}\``);
      }
    }
  }
  for (const [key, schema] of Object.entries(settings)) {
    const scope = schema?.scope;
    if (scope !== undefined && !SCOPES.has(scope)) {
      r.error("M009", `setting \`${key}\` has unknown scope \`${scope}\``);
    }
  }
  if (JSON.stringify(contributes.configuration ?? {}).includes("$ref")) {
    r.error("M010", "`$ref` is not supported in configuration schemas");
  }
}

function checkCapabilities(m, r) {
  const caps = m.capabilities ?? {};
  const trust = caps.untrustedWorkspaces;
  const settings = settingsOf(m.contributes ?? {});
  if (trust === undefined && (m.main || m.browser)) {
    r.warn(
      "M021",
      "no capabilities.untrustedWorkspaces: the extension is disabled in Restricted Mode",
    );
  }
  if (trust !== undefined) {
    const supported = isObject(trust) ? trust.supported : undefined;
    if (![true, false, "limited"].includes(supported)) {
      r.error("M011", "untrustedWorkspaces.supported must be true, false, or 'limited'");
    } else if (supported !== true && !trust.description) {
      r.error(
        "M011",
        "untrustedWorkspaces needs a description when supported is false or 'limited'",
      );
    }
    for (const key of (isObject(trust) && trust.restrictedConfigurations) || []) {
      if (!(key in settings)) {
        r.error("M012", `restrictedConfigurations names undeclared setting \`${key}\``);
      }
    }
  }
  const virtual = caps.virtualWorkspaces;
  if (virtual === undefined || typeof virtual === "boolean") return;
  if (!isObject(virtual) || ![false, "limited"].includes(virtual.supported)) {
    r.error(
      "M013",
      "virtualWorkspaces must be true, false, or {supported: false|'limited', description}",
    );
  } else if (!virtual.description) {
    r.error("M013", "virtualWorkspaces object needs a description");
  }
}

function* walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true }).sort((a, b) =>
    a.name.localeCompare(b.name),
  )) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) yield* walk(path);
    else yield path;
  }
}

const escapeRegExp = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

function checkCommands(m, sources, r) {
  const contributes = m.contributes ?? {};
  const commands = (contributes.commands ?? []).map((c) => c.command);
  const declared = new Set(commands);
  for (const [menu, items] of Object.entries(contributes.menus ?? {})) {
    for (const item of items) {
      if (item.command !== undefined && !declared.has(item.command)) {
        r.error("M014", `menu \`${menu}\` references undeclared command \`${item.command}\``);
      }
    }
  }
  if (sources.length > 0) {
    const text = sources
      .flatMap((root) => [...walk(root)])
      .filter((path) => SOURCE.test(path))
      .map((path) => readFileSync(path, "utf8"))
      .join("\n");
    for (const command of commands) {
      const pattern = new RegExp(`registerCommand\\(\\s*['"\`]${escapeRegExp(command)}`);
      if (!pattern.test(text)) {
        r.error("M015", `command \`${command}\` is contributed but never passed to registerCommand`);
      }
    }
  }
  const events = m.activationEvents ?? [];
  if (events.includes("*")) {
    r.warn("M017", "`*` activates at startup; use a specific event");
  }
  const floor = engineFloor(m.engines?.vscode);
  if (floor && below(floor, [1, 74])) {
    for (const command of commands) {
      if (!events.includes(`onCommand:${command}`)) {
        r.error(
          "M016",
          `engines floor ${floor[0]}.${floor[1]} < 1.74: add \`onCommand:${command}\` to activationEvents`,
        );
      }
    }
  }
}

function checkEntries(m, root, r) {
  for (const field of ["main", "browser"]) {
    const entry = m[field];
    if (typeof entry !== "string") continue;
    const path = resolve(root, entry);
    if (!existsSync(path) && !existsSync(`${path}.js`)) {
      r.error("M018", `\`${field}\` points to missing file \`${entry}\``);
    }
  }
}

function checkTooling(m, preRelease, r) {
  const floor = engineFloor(m.engines?.vscode);
  if (!floor) return;
  if (preRelease && below(floor, [1, 63])) {
    r.error("M019", "pre-release packages need engines.vscode >= 1.63");
  }
  const types = m.devDependencies?.["@types/vscode"];
  const typesFloor = typeof types === "string" ? engineFloor(types) : null;
  if (typesFloor && below(floor, typesFloor)) {
    r.error(
      "M020",
      `@types/vscode ${types} is newer than the engines floor ${floor[0]}.${floor[1]}; APIs past the floor type-check but fail on older hosts`,
    );
  }
}

export function check(manifestPath, { sources = [], built = false, preRelease = false } = {}) {
  const m = JSON.parse(readFileSync(manifestPath, "utf8"));
  if (!isObject(m)) throw new Error("package.json is not a JSON object");
  const r = new Report();
  checkIdentity(m, r);
  checkConfiguration(m.contributes ?? {}, r);
  checkCapabilities(m, r);
  checkCommands(m, sources, r);
  if (built) checkEntries(m, dirname(manifestPath), r);
  checkTooling(m, preRelease, r);
  return r;
}

export function main(argv) {
  let parsed;
  try {
    parsed = parseArgs({
      args: argv,
      allowPositionals: true,
      options: {
        src: { type: "string", multiple: true, default: [] },
        built: { type: "boolean", default: false },
        "pre-release": { type: "boolean", default: false },
        json: { type: "boolean", default: false },
        help: { type: "boolean", short: "h", default: false },
      },
    });
  } catch (error) {
    console.error(`${error.message}\n\n${HELP}`);
    return 2;
  }
  const { values, positionals } = parsed;
  if (values.help) {
    process.stdout.write(HELP);
    return 0;
  }
  if (positionals.length !== 1) {
    console.error(`expected one PACKAGE_JSON argument\n\n${HELP}`);
    return 2;
  }
  let report;
  try {
    report = check(positionals[0], {
      sources: values.src,
      built: values.built,
      preRelease: values["pre-release"],
    });
  } catch (error) {
    console.error(
      `cannot check ${positionals[0]}: ${error.message}; expected a readable package.json holding a JSON object`,
    );
    return 2;
  }
  const warnings = report.findings.length - report.errors;
  if (values.json) {
    console.log(JSON.stringify({ findings: report.findings, errors: report.errors, warnings }, null, 2));
  } else {
    for (const line of report.lines) console.log(line);
    console.log(`${report.errors} error(s), ${warnings} warning(s)`);
  }
  return report.errors ? 1 : 0;
}

if (import.meta.main) process.exit(main(process.argv.slice(2)));
