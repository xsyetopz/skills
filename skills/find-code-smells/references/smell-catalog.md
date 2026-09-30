# Smell catalog

The 24 smells in chapter 3 of Martin Fowler's *Refactoring* (2nd ed.,
2018), grouped by what a reviewer sees. The names are the chapter's
headings ([table of contents][toc]). The signals, measures, and
exceptions below are this skill's working descriptions, not quotations
from the book: when a report quotes a definition, cite the book.

Fix routes name refactorings from Fowler's [online catalog][catalog].
Open the catalog entry before citing its mechanics. Secondary sites such
as refactoring.guru use some first-edition names, for example Lazy Class
and Inappropriate Intimacy; match a smell by its description, not only by
its name.

## Contents

- [Entry format](#entry-format)
- [Names](#names)
- [Duplication](#duplication)
- [Size and control flow](#size-and-control-flow)
- [Data](#data)
- [Coupling between parts](#coupling-between-parts)
- [Unneeded elements](#unneeded-elements)
- [Inheritance](#inheritance)

## Entry format

Each smell lists:

- **Look for.** What to read or search for in the code.
- **Measure.** A tool rule or a count that makes the lead concrete. The
  defaults are listed in [tool thresholds](tool-thresholds.md).
- **Fix route.** The refactorings that usually remove it, and the skill
  that applies them.
- **Keep if.** A condition under which the code is not a smell. Drop the
  lead and say which condition applied.

## Names

### Mysterious Name

- **Look for.** Names that do not say what a function does or what a
  variable holds: `data`, `tmp`, `process`, `handle2`, abbreviations
  only the author knows, and a name that contradicts its body.
- **Measure.** No tool decides meaning. Quote the name, its definition,
  and one call site that a reader cannot follow without opening it.
- **Fix route.** Change Function Declaration, Rename Variable, Rename
  Field (`$write-readable-code`). A name that cannot be found often means
  the unit does two things: split it first.
- **Keep if.** The name is a domain term, a standard abbreviation (`id`,
  `url`), or a short loop index in a few lines.

## Duplication

### Duplicated Code

- **Look for.** The same statements, or the same shape with different
  literals, in several functions or files; parallel `if` chains that must
  be edited together.
- **Measure.** A duplicate detector: PMD CPD, jscpd, Pylint R0801, or
  golangci-lint `dupl`. Report the token or line count used and each
  location pair.
- **Fix route.** Extract Function, Slide Statements to line up the
  common part, Pull Up Method for duplicates in sibling classes
  (`$write-readable-code`).
- **Keep if.** The copies express different rules that happen to look
  alike today, and will change for different reasons. Merging them would
  couple the two rules. Test setup repeated for readability is also not
  a smell.

### Alternative Classes with Different Interfaces

- **Look for.** Two classes or modules that do the same job with
  different method names or signatures, so a caller cannot swap one for
  the other.
- **Measure.** List the matching operations side by side with their
  names and signatures.
- **Fix route.** Change Function Declaration to align names, Move
  Function, then Extract Superclass or a shared interface.
- **Keep if.** The two follow the conventions of two external APIs that
  they wrap, and callers never choose between them.

## Size and control flow

### Long Function

- **Look for.** Functions a reader must scroll, sections separated by
  comments, and several levels of nesting.
- **Measure.** `max-lines-per-function`, `funlen`, `LongMethod`,
  `Metrics/MethodLength`, or `function_body_length`; for Python,
  `$write-readable-code`'s `python_function_metrics.py`. Report
  complexity (`complexity`, C901, `gocognit`) next to the length.
- **Fix route.** Extract Function, Decompose Conditional, Replace Temp
  with Query, Split Phase (`$write-readable-code`, function-shape cards).
- **Keep if.** The body is a flat table of cases or a sequence a reader
  follows top to bottom, and splitting it would scatter one idea.

### Long Parameter List

- **Look for.** Functions with many parameters, several of the same type
  next to each other, or boolean flags that switch behavior.
- **Measure.** `max-params`, Pylint `max-args`, Ruff PLR0913, Clippy
  `too_many_arguments`, Checkstyle `ParameterNumber`.
- **Fix route.** Introduce Parameter Object, Preserve Whole Object,
  Remove Flag Argument, Combine Functions into Class.
- **Keep if.** The function is a constructor or factory whose parameters
  are the object's independent fields, and the language has keyword
  arguments that name each one at the call site.

### Large Class

- **Look for.** A class with many fields, many methods, or groups of
  fields that are used only together, often with a vague name such as
  `Manager` or `Processor`.
- **Measure.** detekt `LargeClass` and `TooManyFunctions`, SwiftLint
  `type_body_length`, RuboCop `Metrics/ClassLength`, Pylint
  `max-attributes` and `max-public-methods`, PMD `GodClass`. For a whole
  file, `$write-readable-code`'s `file_length.py`.
- **Fix route.** Extract Class along the field groups, Extract Superclass,
  Replace Type Code with Subclasses.
- **Keep if.** The class is a generated client, or a facade whose methods
  each forward to one collaborator and hold no logic.

### Repeated Switches

- **Look for.** The same `switch`, `match`, or `if`/`elif` chain on the
  same type code in several places, so a new case needs edits in each.
- **Measure.** Search for the discriminant, for example
  `rg -n 'case .*Kind\.|kind ==' src/`, and count the sites that branch
  on it.
- **Fix route.** Replace Conditional with Polymorphism, or one dispatch
  table that all sites share (`$write-readable-code`).
- **Keep if.** There is one switch, or the language checks that every
  match covers every case (Rust `match`, TypeScript `never` checks) and
  the cases are few.

### Loops

- **Look for.** A loop that filters, maps, and accumulates by hand, where
  the language has a pipeline form that names each step.
- **Measure.** Read the loop body; count the separate jobs it does.
- **Fix route.** Replace Loop with Pipeline, Split Loop.
- **Keep if.** The loop is faster in a measured hot path, or a pipeline
  would hide an early exit or a side effect.

## Data

### Global Data

- **Look for.** Module-level or static state that any code can write:
  singletons with setters, mutable module variables, environment reads
  scattered through the code.
- **Measure.** List every writer of the global; count the files.
- **Fix route.** Encapsulate Variable, then narrow its scope and pass it
  in.
- **Keep if.** The value is a constant, or it is written once at start-up
  and read-only after that.

### Mutable Data

- **Look for.** Values changed in place far from where they were made, so
  a reader cannot tell which update a later line sees.
- **Measure.** List the writers of the field or variable between its
  creation and its use.
- **Fix route.** Encapsulate Variable, Split Variable, Separate Query
  from Modifier, Change Reference to Value.
- **Keep if.** The mutation is local to one short function, or measured
  performance needs it.

### Data Clumps

- **Look for.** The same group of fields or parameters traveling together:
  `start`, `end`, `timezone`; `street`, `city`, `postcode`.
- **Measure.** Search for the group in signatures and count the sites.
- **Fix route.** Extract Class, Introduce Parameter Object.
- **Keep if.** The items appear together only by chance and change
  independently.

### Primitive Obsession

- **Look for.** Strings, numbers, or dicts standing in for domain
  concepts: money as `float`, a phone number as `str`, status codes as
  string literals compared across the code.
- **Measure.** Count the sites that validate or parse the same primitive.
- **Fix route.** Replace Primitive with Object, Replace Type Code with
  Subclasses, Introduce Parameter Object.
- **Keep if.** The value has no rules beyond its type and crosses a
  boundary (a JSON field) where it is converted once.

### Temporary Field

- **Look for.** A field that is set and read only in some cases and holds
  a placeholder the rest of the time.
- **Measure.** List the methods that read the field and the paths that
  leave it empty.
- **Fix route.** Extract Class for the field and the code that uses it;
  Introduce Special Case for the empty path.
- **Keep if.** The field is a documented cache with a clear invalidation
  rule.

### Data Class

- **Look for.** A class with only fields and accessors while the logic
  that uses its data lives in other classes.
- **Measure.** List the callers that compute from its fields.
- **Fix route.** Move Function into the class, Encapsulate Record, Remove
  Setting Method.
- **Keep if.** It is an immutable record at a boundary (a DTO, a parsed
  message, a `dataclass` returned from a split phase).

## Coupling between parts

Coupling seen in the code. Coupling seen in the history (files that
change together) is in [change coupling](change-coupling.md).

### Feature Envy

- **Look for.** A method that reads another object's fields more than its
  own.
- **Measure.** Count the references to each object inside the method.
- **Fix route.** Move Function to the class whose data it uses, after
  Extract Function if only part of it envies.
- **Keep if.** The method belongs to a strategy or visitor that is meant
  to keep behavior apart from the data.

### Message Chains

- **Look for.** `a.b().c().d()` walks where the caller depends on every
  step's structure.
- **Measure.** Search for chains of three or more navigation calls, and
  count the callers of the same chain.
- **Fix route.** Hide Delegate, or Extract Function and Move Function to
  put the walk in one place.
- **Keep if.** The chain is a fluent builder or a pipeline where each call
  returns the same kind of value.

### Middle Man

- **Look for.** A class whose methods mostly forward to one other class.
- **Measure.** Count the forwarding methods against the total.
- **Fix route.** Remove Middle Man, Inline Function.
- **Keep if.** The class is a deliberate adapter or facade at a boundary
  (see `$design-software-architecture`).

### Insider Trading

- **Look for.** Modules that read or write each other's internals, or
  private data passed back and forth, so neither can change alone.
- **Measure.** List the imports of private names or internal packages
  across the pair, and run `scripts/change_coupling.py` for the pair.
- **Fix route.** Move Function and Move Field to one side, Hide Delegate,
  or a shared module that both depend on; for package-level cycles, use
  `$design-software-architecture`.
- **Keep if.** The two are one unit split for size and are always released
  together; then consider merging them.

### Divergent Change

One module changes for several unrelated reasons. The history test and
the fix are in [change coupling](change-coupling.md#divergent-change).

### Shotgun Surgery

One change needs small edits in many modules. The history test and the
fix are in [change coupling](change-coupling.md#shotgun-surgery).

## Unneeded elements

### Lazy Element

- **Look for.** A function, class, or module that adds a name but no
  meaning: a wrapper that renames one call, a class with one trivial
  method.
- **Measure.** Count the element's lines and callers.
- **Fix route.** Inline Function, Inline Class, Collapse Hierarchy.
- **Keep if.** The name documents intent that the inlined code would lose,
  or the element is a seam that tests or a second implementation use.

### Speculative Generality

- **Look for.** Hooks, parameters, abstract classes, and options that no
  caller uses, added for a future need.
- **Measure.** Find the callers; list the parameters always passed the
  same value and the interfaces with one implementation.
- **Fix route.** Collapse Hierarchy, Inline Function, Remove Dead Code,
  Change Function Declaration to drop the parameter.
- **Keep if.** A public API promises the extension point, or a second
  implementation exists in tests or in another repository.

### Comments

- **Look for.** Comments that explain what unclear code does, instead of
  why it does it.
- **Measure.** Read each comment against the code under it.
- **Fix route.** Extract Function named after the comment, Rename,
  Introduce Assertion (`$write-readable-code`).
- **Keep if.** The comment gives a reason, a constraint, or a source that
  the code cannot state.

## Inheritance

### Refused Bequest

- **Look for.** A subclass that ignores or overrides with no-ops most of
  what it inherits.
- **Measure.** List the inherited members the subclass uses and those it
  overrides to do nothing or to throw.
- **Fix route.** Push Down Method and Push Down Field, or Replace
  Subclass with Delegate and Replace Superclass with Delegate.
- **Keep if.** The subclass reuses behavior and refuses only a little
  implementation, while it still honors the superclass interface.

[toc]: https://informit.com/store/refactoring-improving-the-design-of-existing-code-9780134757711
[catalog]: https://refactoring.com/catalog/
