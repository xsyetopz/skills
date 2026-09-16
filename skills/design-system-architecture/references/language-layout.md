# Organize software modules using native language mechanisms

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

## Local reasoning

Keep the repository's established terms for the same domain concepts. Make
units, ownership, side effects and failure boundaries visible where they affect
safe changes; a distinct type is useful when confusing two values is a realistic
error, not merely because both are strings. Keep invariant enforcement close to
the operation it protects. Extract a named responsibility when it reduces what a
reader must reconstruct, not just because two blocks look alike.

Judge readability through a concrete change: can a maintainer locate the owner,
follow the normal and failure paths, and identify the invariant that must remain
true? Do not translate language-proficiency labels into programmer levels or
impose imported function/parameter quotas. Existing configured limits still
apply. Names and comments should clarify intent rather than compensate for
unnecessary indirection. [Review guidance][review].

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

## .NET languages

Do not apply one .NET-wide source skeleton. In F#, namespaces contain types and
modules, not direct value/function bindings; put those bindings in a module. A
template with `namespace Example` followed by a top-level `let` is not a valid
namespace layout. [F# namespaces][fsharp].

For C#, distinguish assembly visibility from file visibility. `internal` is not
file-private; a `file` top-level type is restricted to its declaring source file
when supported by the selected language version. A file-local implementation
type cannot leak through a non-file-local type's member signatures. Use these
boundaries for actual ownership, not to generate an empty class at every
visibility level. [C# file-local types][csharp-file].

## C and C++

In C, distinguish scope from linkage. A file-scope `static` function has
internal linkage; placing a declaration in a header does not make an
implementation private. Put the intended cross-translation-unit declarations in
a guarded, self-contained header and keep private helpers with their
implementation. Check that a consumer includes the header without relying on
another include's order. The C23 working draft describes scope and linkage
separately; use the project's selected C standard and compiler. [WG14 draft,
sections 6.2.1–6.2.2][c-linkage].

In C++, keep declarations and definitions consistent with the one-definition
rule, including templates and inline entities. Do not place ordinary non-inline
external definitions in a widely included header. Include required dependencies
instead of relying on incidental transitive includes; avoid namespace-wide
`using` directives in headers. Existing header or module conventions govern:
adopting modules is a build/toolchain decision, not cosmetic file cleanup. A
header/implementation pair per tiny type is not required. These are [Core
Guidelines source-organization recommendations][cpp-layout], not a prescribed
architecture. Compile and link a real consumer after changing the public
surface.

## Java

Packages and modules are different boundaries. Package-private access does not
extend to a similarly named subpackage. A public type in a named module also
needs the appropriate exported package and module readability for ordinary
external use; an `opens` directive serves reflective access, not the same
contract as `exports`. Keep package structure consistent with the existing
source roots and build tool. [JLS packages and modules][java-layout].

Keep mutually dependent package-private helpers near their owning package rather
than making them public solely to cross a newly invented directory boundary. Do
not introduce a named module or split a build artifact just to reorganize a few
files. Test the actual supported classpath/module-path and downstream import
configuration; a successful IDE build can hide packaging differences.

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
[fsharp]:
https://learn.microsoft.com/en-us/dotnet/fsharp/language-reference/namespaces
[csharp-file]:
https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/file
[c-linkage]: https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3096.pdf
[cpp-layout]:
https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#S-source
[java-layout]: https://docs.oracle.com/javase/specs/jls/se25/html/jls-7.html
