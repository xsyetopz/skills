# Test design and implementation coupling

Load this reference for implementation-sensitive assertions, refactor safety,
smell diagnosis, or legitimate structural evidence.

## Distinguish contract from implementation

A contract states required values, errors, transitions, effects, and prohibited
effects for a consumer at the selected boundary. That consumer may be a
component, not a human. Black-box reasoning derives cases from that contract; it
does not require running the whole system or ignoring code when diagnosing
failures. A public method is a useful entrypoint, but not every property visible
through it is promised behavior.

Helpers, algorithms, internal collections, decomposition, and incidental order
are replaceable unless an independent requirement constrains them. Ask whether a
correct alternative can fail the test, and whether a meaningful wrong result can
pass. Passing today is insufficient evidence of useful protection.

The established smell **Overspecified Software**, also called **Overcoupled
Test**, constrains how software is built beyond what it must accomplish. See the
[Test Smell Catalog][overspecified]. **Fragile Test** is the broader maintenance
symptom; implementation coupling is one cause, not a synonym for every fragile
test. [Seemann][seemann] explains this relationship, while [Meszaros's publisher
chapter][meszaros] discusses interaction sensitivity in test doubles. These
sources do not imply that every double is harmful.

## Public consequence instead of private evidence

**Deciding condition:** `render_name(" Ada ")` must return `"Ada"`; no helper or
source spelling is promised. These are alternative tests of that same rule.

### Defect: freeze helper names and source text

```python
from inspect import getsource

assert "_trim" in getsource(render_name)
assert _trim(" Ada ") == "Ada"
```

The helper can work while the public operation ignores its result. Inlining it
also breaks the test without changing the contract.

### Correction: execute the consumer's operation

```python
assert render_name(" Ada ") == "Ada"
```

This checks the promised result, independent of helper extraction.

Check: corrected example must pass delegated and inline `strip()`
implementations and fail an implementation that calls `_trim` but returns the
original input. defective example passes that fault and rejects the inline
implementation's source. Do not add public APIs merely to expose private helpers
to tests.

## Values instead of internal representation

**Deciding condition:** a basket reports the number of books added. Its storage
type is not a consumer guarantee; adding twice must report two.

### Defect: pin the private collection

```python
basket = Basket()
basket.add("book")
basket.add("book")
assert basket._items == ["book", "book"]
```

This rejects a correct counting map and can miss a faulty public count method.

### Correction: check the contractual quantity

```python
basket = Basket()
basket.add("book")
basket.add("book")

assert basket.count("book") == 2
```

The two additions establish the duplicate-quantity scenario, not a phase error.

Check: corrected example passes list-backed and counting-map baskets; it fails
when `count("book")` returns one after both additions. defective example still
passes a list-backed basket with that faulty count method. Collection assertions
remain appropriate when the collection's values or order are the actual returned
contract.

## Architecture constraints instead of frozen declarations

Source inspection is legitimate when source is the product/input (for example, a
source transformer) or an explicit structural rule is being checked. It does not
prove runtime behavior. [ArchUnit][archunit] supports package dependency, layer,
and cycle rules over imported classes. Selecting only independently established
constraints is this skill's synthesis, not a universal ArchUnit policy. Use the
repository's existing structural analysis mechanism.

**Deciding condition:** an agreed architecture forbids dependencies from domain
to transport. It does not freeze domain class names or decomposition.

### Defect: snapshot the class arrangement

```python
assert domain_classes == {"Order", "OrderService"}
```

This rejects an allowed class extraction yet admits a forbidden dependency.

### Correction: enforce the actual dependency rule

```python
assert not any(
    origin == "domain" and target == "transport"
    for origin, target in dependency_edges
)
```

Here `dependency_edges` comes from the established analyzer, not a hand-written
list pretending to describe production. Its nodes are architectural layers.

Check: with the same domain/transport fixture, extract a domain class: corrected
example still passes while defective example fails. Add a domain-to-transport
edge without renaming classes: corrected example fails while defective example
passes. Manually confirm the rule's authority, analyzer scope, and treatment of
generated/dynamic dependencies. A synthetic edge check tests the predicate, not
the analyzer's completeness.

[overspecified]: https://test-smell-catalog.readthedocs.io/en/latest/Code%20related/In%20association%20with%20production%20code/Overspecified%20Software.html
[seemann]:
https://blog.ploeh.dk/2019/02/18/from-interaction-based-to-state-based-testing/
[meszaros]: https://www.informit.com/content/images/9780131495050/samplechapter/0131495054_CH23.pdf
[archunit]: https://www.archunit.org/userguide/html/000_Index.html
