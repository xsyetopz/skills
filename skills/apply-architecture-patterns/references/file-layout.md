# File Layout

Read when creating a source file or reordering one.
The repository's formatter, linter, and the neighboring files win over this page.
Then read the file for the language in `layouts/`, which `SKILL.md` lists.

## Contents

- [Decision Order](#decision-order)
- [Visibility](#visibility)
- [Order Within a File](#order-within-a-file)
- [Tests](#tests)
- [Adding a Language](#adding-a-language)

## Decision Order

1. Find the language's real visibility model:
   keywords, capitalization, naming convention, or an export list.
1. Give each declaration the narrowest visibility that works.
1. Widen only for a real caller across that boundary, and name the caller.
1. Order declarations by semantic role, not by visibility bucket.
1. Keep a declaration next to its implementation where the language allows it.
1. Put tests where the ecosystem expects them.
1. Keep the language's own conventions.
   Do not copy another language's model into it.

## Visibility

- A new declaration starts private to its scope, file, or module.
- Widening to the package, module, or crate needs an existing caller there.
- Public API is a decision about callers outside the project, so ask before adding to it.
- Do not widen a declaration so a test can reach it.
  Test through the public surface, or use the language's test-only access.
- Where privacy is only a naming convention (Python, Ruby `protected`),
  keep the module's public surface explicit,
  such as `__all__` or an export list.

## Order Within a File

The layout files give the exact order.
The shape is the same in every language:

1. Header: license, language directives, and the package or namespace declaration.
1. Imports, in the formatter's groups.
1. Constants and file-level values.
1. The main type with its members together, then the types and functions that support it.
1. Private helpers last, next to the code that uses them.

Inside a type, order by role:
constants, state, construction, public behavior, then internal behavior.
Never split a type from its members to group by visibility.
A new declaration goes where its role belongs in the existing order, not at the end of the file.
If a file already follows another order, follow it and do not reorder it.

## Tests

- Put tests where the build tool and the language community expect them: beside the code,
  in a mirrored test tree, or in a test project.
- Do not add inline test blocks to a language that does not use them.
- A test file follows the same layout rules as source.

## Adding a Language

1. Create `layouts/<language>.md` with an ordering list of at most ten items.
1. Add one template as a fenced code block that holds only the skeleton and short comments.
1. Cover visibility, the order in a file, where tests go, and each invariant the language adds.
1. Include a Mermaid graph only if it carries information a list cannot.
1. Check each construct against the current language release and its official documentation.
1. Link the new file from `SKILL.md`.
