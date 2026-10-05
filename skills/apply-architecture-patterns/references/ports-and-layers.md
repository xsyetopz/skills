# Ports and Layers

Read when the codebase is hexagonal, clean, onion, or layered, or when you must check which way
imports point between layers.

## Contents

- [One Rule Under Four Names](#one-rule-under-four-names)
- [Recognize the Style](#recognize-the-style)
- [Where Code Goes](#where-code-goes)
- [Enforce the Direction](#enforce-the-direction)
- [Agent Mistakes](#agent-mistakes)
- [Example](#example)

## One Rule Under Four Names

Hexagonal, onion, clean, and layered architecture differ in drawing and vocabulary. They share one
rule: business code does not depend on delivery or storage code.

- Hexagonal (Cockburn): "The rule to obey is that code pertaining to the inside part should not
  leak into the outside part." The root cause it targets is "the entanglement between the business
  logic and the interaction with external entities."
  <https://alistair.cockburn.us/hexagonal-architecture/>
- Onion (Palermo): "all code can depend on layers more central, but code cannot depend on layers
  further out from the core. In other words, all coupling is toward the center."
  <https://jeffreypalermo.com/2008/07/the-onion-architecture-part-1/>
- Clean (Martin): "source code dependencies can only point inwards. Nothing in an inner circle can
  know anything at all about something in an outer circle."
  <https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html>
- Layered (Fowler): "presentation depends on the domain, which then depends on the data source."
  A common variation adds a mapper so the domain does not depend on its data sources.
  <https://martinfowler.com/bliki/PresentationDomainDataLayering.html>

The shapes are schematic. The hexagon is drawn "to allow the people doing the drawing to have room
to insert ports and adapters as they need", and Martin allows more than four circles, but "The
Dependency Rule always applies." Extra layers such as a service layer do not break layering
(Fowler, same page). Count the rule, not the circles.

## Recognize the Style

Name the style with evidence, not folder names. Check these in order:

1. Import direction. Pick the domain package and list what it imports. A domain that imports a
   framework, ORM, HTTP client, or UI type is not hexagonal, onion, or clean, whatever the folders
   say.
1. Interfaces in the core. Hexagonal and onion put the repository or gateway interface inside the
   core and the implementation outside: "Only the interface is in the application core." (Palermo,
   part 1.) Look for constructors that accept an interface (Cockburn's sample passes a repository
   adapter into the application, real or mock).
1. Wiring. An IoC container, a composition root, or a `main` that builds adapters and hands them
   inward. Palermo's part 2 describes a container wiring implementations at runtime.
   <https://jeffreypalermo.com/2008/07/the-onion-architecture-part-2/>
1. Rules in the repository. An import-linter contract, a dependency-cruiser config, an ArchUnit
   test, or crate boundaries (see below). A rule file is stronger evidence than a diagram.
1. The nearest similar feature, read from entry point to storage.

If the evidence is a plain presentation, domain, and data split with calls going one way, the style
is layered. Say which style the nearest feature uses when the codebase mixes them.

## Where Code Goes

| Kind of code | Owner |
| --- | --- |
| Business rules that hold for the enterprise | Entities or domain model (clean: "Enterprise wide business rules") |
| Application-specific rules and the flow of data to and from entities | Use cases or application services (clean: "orchestrate the flow of data to and from the entities") |
| Interface that the core needs (repository, gateway, clock, publisher) | The core, as a port |
| Controller, REST or GraphQL handler, CLI command, message consumer | Primary (driving) adapter |
| Repository implementation, service client, message producer | Secondary (driven) adapter |
| Framework setup and wiring | The outermost layer, which is "glue code" in Martin's words |

Cockburn names the two sides primary and secondary adapters, "also called driving adapters and
driven adapters." The controller and repository examples are from a third-party summary, not
Cockburn: <https://herbertograca.com/2017/09/14/ports-adapters-architecture/>.

An adapter converts an outside event into a call on the application: "As events arrive from the
outside world at a port, a technology-specific adapter converts it" into a procedure call. The
functional specification is made against the inner hexagon, not "any one of the external
technologies". So a controller parses input, calls one use case, and maps the result. In Martin's
terms, controllers, presenters, and views are interface adapters and hold no business rules.

Data crossing a boundary uses the inner shape. Martin: the name of something declared in an outer
circle "must not be mentioned by the code in the an inner circle", and framework-generated data
formats must not be used by inner circles. Map an ORM row or request DTO to a domain type at the
adapter.

Layers are not only for big programs: "A small program may just put separate functions for the
layers into different files." (Fowler.)

## Enforce the Direction

Use the tool the repository already has, and run it after the change. If it has none, say so in
the report and do not add one unasked.

| Ecosystem | Tool | What the docs show |
| --- | --- | --- |
| Python | import-linter | Contract types: forbidden, protected, layers, independence, acyclic siblings. A layers contract enforces "a 'layered architecture', where higher layers may depend on lower layers, but not the other way around", and includes indirect imports. Forbidden contracts take `source_modules`, `forbidden_modules`, and `broken_contract_guidance`. |
| TypeScript, JavaScript | dependency-cruiser | `forbidden` rules with `from` and `to`, such as `"name": "not-to-core-http"`, `"from": {}`, `"to": { "path": "http" }`. |
| JVM | ArchUnit | `layeredArchitecture()` with `.layer("Controller").definedBy("..controller..")`, then `.whereLayer("Controller").mayNotBeAccessedByAnyLayer()` and `.whereLayer("Service").mayOnlyBeAccessedByLayers("Controller")`. |
| .NET | NetArchTest, ArchUnitNET | Fluent rules in unit tests, such as `.ResideInNamespace(...).ShouldNot()...` (NetArchTest) or `Types().That().ResideInAssembly(...).As("Example Layer")` (ArchUnitNET). |
| Rust | cargo workspace | A workspace is "a collection of one or more packages, called workspace members". A crate can use only what is in its `[dependencies]`, so crate boundaries bound the direction (inferred from cargo's model; cargo also rejects cyclic crate dependencies, which the source does not state). |

Sources: <https://import-linter.readthedocs.io/en/stable/contract_types/>,
<https://github.com/sverweij/dependency-cruiser/blob/main/doc/rules-tutorial.md>,
<https://www.archunit.org/userguide/html/000_Index.html> (section 4.6, Layer Checks),
<https://github.com/BenMorris/NetArchTest/blob/master/README.md>,
<https://github.com/TNG/ArchUnitNET>,
<https://doc.rust-lang.org/cargo/reference/workspaces.html>.

Read the rule file for the exact config keys of the installed version. This file does not give
command lines.

## Agent Mistakes

- A new endpoint that puts the rule in the handler or SQL. Move it to a use case or domain type.
- A domain or application file that imports the ORM, an HTTP client, a cloud SDK, or a framework
  type "just for the type". Add a port in the core and implement it in an adapter.
- Returning an ORM row or request DTO from a use case. Map at the adapter.
- A new port, layer, or mapper that no existing feature has. This is speculative generality; follow
  the nearest feature or ask. A port with one adapter and no test double earns nothing yet.
- The reverse error: removing layers because Fowler's YAGNI argument sounds like a reason. Fowler
  uses layering even without testability or substitutability reasons, so do not collapse existing
  layers in the name of YAGNI. <https://martinfowler.com/bliki/PresentationDomainDataLayering.html>
- Making the domain anemic: types that are "little more than bags of getters and setters" with all
  behavior in services. Fowler calls it an anti-pattern, yet he also says a service layer is fine
  with a rich domain model and that "Domain Models aren't always the best tool" (Transaction
  Scripts exist). Follow what the codebase does and name the choice.
  <https://martinfowler.com/bliki/AnemicDomainModel.html>
- Fixing a failing architecture test by loosening the rule. Fix the import.
- Starting a migration to another style unasked. Name the problem with `file:line` and ask.

## Example

A port in the core, an adapter outside, wiring at the edge (Python):

```python
# app/core/ports.py  (imports nothing outside the core)
from typing import Protocol

class InvoiceRepository(Protocol):
    def save(self, invoice: "Invoice") -> None: ...

# app/core/issue_invoice.py
def issue_invoice(repo: InvoiceRepository, order: "Order") -> "Invoice":
    invoice = Invoice.from_order(order)   # rule lives in the domain type
    repo.save(invoice)
    return invoice

# app/adapters/sql_invoice_repository.py  (depends inward on the core)
class SqlInvoiceRepository:
    def save(self, invoice: Invoice) -> None:
        ...  # map to a row, write with the database client

# app/adapters/http.py  (primary adapter: parse, call one use case, map)
def post_invoice(request):
    order = parse_order(request.json)
    return to_response(issue_invoice(repo, order))
```

The matching import-linter contract, as an INI-style sketch (check the keys against the installed
version):

```ini
[importlinter:contract:core-is-inner]
name = Core imports no adapters
type = forbidden
source_modules = app.core
forbidden_modules = app.adapters
```
