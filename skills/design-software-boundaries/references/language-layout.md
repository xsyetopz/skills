# Language-native layout and local reasoning

Use the project's formatter, build manifest, runtime/module mode, public API,
and neighboring code as constraints. Do not reorder declarations or create files
just to match a cross-language template. Keep related contractual types
together: `Token`, `TokenKind`, and a small `TokenStream` can share one module
when they co-evolve. Split where visibility, lifecycle, independent use, or
build ownership actually differs.

Review the public surface and the number of concepts needed to make a change,
not only file length. A long sequential function can be clearer than a chain of
tiny one-use helpers. Avoid speculative generic types, abstract factories, and
empty interfaces. These are review recommendations consistent with [Google's
complexity review guidance][review], not empirical universal LOC or complexity
thresholds. A threshold from imported notes is not a language rule.

## Python

[PEP 8][python] gives precedence to project conventions. Keep imports at the
top, grouped as standard library, third party, and application-local. Module
dunder names such as `__all__` precede ordinary imports but follow future
imports. Use a leading underscore for a non-public interface; double-leading
underscores perform class name mangling and are not a general private-access
system. Do not add `__all__` or classes merely to fill a template.

Choose [src versus flat layout][packaging] from packaging needs. A `src/` layout
helps separate the import package from repository files and normally requires
installation; flat layout is simpler but can let local files mask installation
mistakes. For distributed packages, build and install the artifact in an
isolated environment and run an import/behavior test outside the source
checkout. A test that succeeds only because the checkout is on `sys.path` is
insufficient.

## Go

Follow the official [module layout guide][go]. A small package can start at the
module root with colocated tests. Add `cmd/` for multiple commands when useful,
not as a prerequisite for every executable. Use `internal/` for implementation
packages whose imports should be restricted by the toolchain. Do not introduce
`pkg/`, services, repositories, or one package per type by reflex.

Keep package APIs small and coherent; move a type only after checking import
cycles and consumers. Validate the actual module with its configured Go checks,
including tests and build. Public name changes are compatibility changes, not
only file moves.

## Rust

[Rust visibility][rust] distinguishes private items, `pub(super)`, `pub(crate)`,
and exported API. Expose only what consumers need. A file boundary is not itself
an abstraction; closely related types and implementation blocks can remain in
one module. Avoid making an implementation public merely to make tests reach it.
Choose unit tests for private behavior and integration tests for external use.

Before splitting crates, identify independent dependency, feature, compilation,
or release needs. A workspace increases manifest and compatibility work; it is
not required for a modular library. Verify feature combinations actually
supported by the project, public imports, documentation examples, and downstream
use after moving or re-exporting items.

## JavaScript and TypeScript

Use [TypeScript's module reference][typescript] to match resolution and emitted
module format to the real runtime or bundler. A path alias is not automatically
a runtime import mapping. Do not introduce barrels that create cycles or obscure
side-effect order. Keep browser, server, and tooling imports separate where
their APIs differ. Test built artifacts under the supported runtime; type
checking alone does not prove imports resolve after publishing.

## Other languages

Discover the target compiler version, build manifest, module/package visibility,
generated-source ownership, and official style guidance before adding a layout.
Do not transplant Python underscore conventions, Go package rules, or Java's
public-class file naming into another language. Verify the smallest real package
with its native build and a consumer; avoid placeholder imports, empty methods,
and decorative diagrams presented as executable examples.

[review]:
  https://google.github.io/eng-practices/review/reviewer/looking-for.html
[python]: https://peps.python.org/pep-0008/
[packaging]:
  https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/
[go]: https://go.dev/doc/modules/layout
[rust]: https://doc.rust-lang.org/reference/visibility-and-privacy.html
[typescript]:
  https://www.typescriptlang.org/docs/handbook/modules/reference.html
