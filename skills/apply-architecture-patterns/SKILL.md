---
name: apply-architecture-patterns
description: >-
  Places new code in the layer, module, and pattern the codebase already uses: hexagonal ports and
  adapters, clean and onion architecture, layering, MVC, MVP, MVVM, ECS, and GoF patterns such as
  Strategy, Factory, Observer, and Visitor. Use when adding a feature, service, screen, or module,
  or choosing a design pattern. Not for refactoring smells in working code.
when_to_use: >-
  Where should this new endpoint's logic go? Add a payment provider without touching the domain.
  Should I use a factory or a strategy here? My view model talks to the database. Is this
  codebase MVVM or MVC?
---

# Apply Architecture Patterns

New code inherits the architecture around it, or it erodes it. Agents add code where it is easiest
to type: domain rules in a controller or view, a database client imported into the core, a pattern
the codebase has never used, or a second architecture beside the first.

## Rules

- Identify the existing architecture before adding code. Name it with evidence: the directory
  layout, the direction of imports between layers, where a similar feature already lives, and any
  architecture tests or import rules. Do not infer it from folder names alone.
- Copy the nearest existing feature's shape. Put the new code in the same layers, with the same
  kinds of types, names, and wiring. A second way of doing the same thing is a cost every later
  reader pays.
- Keep dependencies pointing inward. Domain and application code import no framework, database,
  HTTP, UI, or file system types. Adapters depend on the core, never the reverse.
- Domain rules live in the domain or application layer, not in controllers, views, view models,
  handlers, or SQL. A controller or view parses input, calls one use case, and maps the result.
- Do not invent a pattern or a layer the codebase does not use. A port with one adapter and no test
  double, a factory with one product, or a strategy with one strategy is speculative generality.
  Add the second implementation first, or ask.
- Prefer the language feature to the GoF pattern: a function for a one-method Strategy or Command,
  a sum type and `match` for a closed Visitor, a module or dependency injection for a Singleton.
- Follow the codebase's architecture unless it causes a defect. Then use the sound form in touched
  code, name the problem with evidence (`file:line`, how often it appears, and its maintenance
  cost), and ask before migrating untouched code. Never start an architecture migration unasked.
- Check dependency direction with a tool when the repository has one (import-linter,
  dependency-cruiser, ArchUnit, NetArchTest, crate boundaries), and run it after the change.
- Report the architecture you identified, where the new code went and why, each rule or tool check
  you ran with its result, and each check you skipped by name.

## Workflow

1. Map the codebase: entry points, layers or modules, and which imports which. Read one existing
   feature end to end, from entry point to storage.
1. Name the style and the evidence. If the codebase mixes styles, name the one the nearest feature
   uses and say so.
1. Place each new type: which layer, which existing interface it implements or calls, and which
   files change. If the change needs a new layer, port, or pattern, ask first.
1. Write the code, then the architecture check and the tests for each layer you touched.
1. Report.

## References

- Read [`references/ports-and-layers.md`](references/ports-and-layers.md) for hexagonal, clean,
  onion, or layered codebases, and for dependency-direction tools.
- Read [`references/ui-patterns.md`](references/ui-patterns.md) for MVC, MVP, or MVVM code, and for
  where logic goes in a screen, view, controller, or view model.
- Read [`references/gof-patterns.md`](references/gof-patterns.md) before adding or naming a GoF
  pattern, to check it fits and is not over-engineering.
- Read [`references/ecs.md`](references/ecs.md) for entity component system code (Bevy, flecs,
  Unity Entities).
