# GoF Patterns

Read before adding or naming a GoF pattern, to check that it fits the codebase and that a function
or a language feature would not do.

## Contents

- [Rules](#rules)
- [Recognize an Existing Pattern](#recognize-an-existing-pattern)
- [When a Language Feature Replaces the Pattern](#when-a-language-feature-replaces-the-pattern)
- [Fits and Over-Engineering](#fits-and-over-engineering)
- [Agent Mistakes](#agent-mistakes)
- [Examples](#examples)

## Rules

- Introduce a pattern from a concrete smell, not first. The Kerievsky catalog is built this way:
  Replace Conditional Logic With Strategy, Replace State-Altering Conditionals with State, Move
  Creation Knowledge To Factory, Replace Hard-Coded Notifications With Observer, and others.
  Reading it as "start from the smell" is an inference from the names.
  <https://www.industriallogic.com/xp/refactoring/catalog.html>
- If the codebase already uses the pattern, copy its naming, file layout, and registration. If it
  does not, ask before the first one.
- Fowler on speculative features: "a capability we presume our software needs in the future should
  not be built now", and the cost of carry is that "this complexity makes it harder to modify and
  debug that software". His test: imagine the later refactoring; "Often that thought experiment is
  enough to convince them that it won't be significantly more expensive to add it later."
  <https://martinfowler.com/bliki/Yagni.html>
- The Speculative Generality smell: "code is created 'just in case' to support anticipated future
  features that never get implemented." <https://refactoring.guru/smells/speculative-generality>
  (secondary source)

The "Fits" and "Over" quotes below come from refactoring.guru (`/design-patterns/<slug>`), a
secondary source; the GoF book was not consulted. Items marked (inferred) are advice, not quotes.

## Recognize an Existing Pattern

Names lie; check the shape. A `*Factory` that only calls `new` once, a `*Strategy` with one
implementation, or a `*Manager` that is a global are not working patterns. Search for the
participants: an interface with several implementations chosen at runtime (Strategy, State), a
subscriber list (Observer), a tree whose nodes share an interface (Composite), a wrapper with the
same interface as what it wraps (Decorator, Proxy). Then add yours the same way.

## When a Language Feature Replaces the Pattern

Norvig (1996) found "16 of 23 patterns are either invisible or simpler" in Lisp or Dylan, through
first-class types, functions, macros, method combination, multimethods, and modules; it is a claim
"for at least some uses of each pattern" in those languages.
<https://norvig.com/design-patterns/design-patterns.pdf>

| Pattern | Use instead, when the language has it |
| --- | --- |
| Strategy | A function value. Anonymous functions let you vary an algorithm "without bloating your code with extra classes and interfaces." <https://refactoring.guru/design-patterns/strategy> |
| Command | A closure (Norvig lists Command under first-class functions; the Rust closures chapter was not read). |
| Visitor | A sum type and pattern matching. JEP 441: "Without such pattern matching, expressing ad-hoc polymorphic calculations like this requires using the cumbersome visitor pattern." <https://openjdk.org/jeps/441> |
| Singleton | A module: Python module statements "are executed only the first time the module name is encountered in an import statement." <https://docs.python.org/3/tutorial/modules.html> The equivalence is inferred. Dependency injection replaces global access (inferred). |
| Iterator | The built-in iterator: "An iterator is responsible for the logic of iterating over each item and determining when the sequence has finished." (Rust) <https://doc.rust-lang.org/book/ch13-02-iterators.html> |
| Builder | Named or default arguments, where the language has them (inferred). |
| Template Method | A function that takes the varying steps as arguments (Norvig lists it under first-class functions). |

## Fits and Over-Engineering

Fits is when to reach for it; Over is its stated cost. All quotes are from
`https://refactoring.guru/design-patterns/<slug>`.

| Pattern | Fits | Over-engineering |
| --- | --- | --- |
| Factory Method | "when you don't know beforehand the exact types and dependencies of the objects your code should work with" | "may become more complicated since you need to introduce a lot of new subclasses" |
| Abstract Factory | "various families of related products, but you don't want it to depend on the concrete classes" | "a lot of new interfaces and classes are introduced" |
| Builder | "get rid of a 'telescoping constructor'" | "requires creating multiple new classes" |
| Prototype | "code shouldn't depend on the concrete classes of objects that you need to copy" | "Cloning complex objects that have circular references might be very tricky." |
| Singleton | "a class in your program should have just a single instance available to all clients" | "can mask bad design", "Violates the Single Responsibility Principle", "difficult to unit test" |
| Adapter | "use some existing class, but its interface isn't compatible with the rest of your code" | "Sometimes it's simpler just to change the service class so that it matches the rest of your code." |
| Bridge | "extend a class in several orthogonal (independent) dimensions" | "make the code more complicated by applying the pattern to a highly cohesive class" |
| Composite | "implement a tree-like object structure" | forces a common interface, so you "overgeneralize the component interface" |
| Decorator | "assign extra behaviors to objects at runtime without breaking the code that uses these objects" | "hard to remove a specific wrapper", order-dependent, "ugly" configuration |
| Facade | "limited but straightforward interface to a complex subsystem" | "A facade can become a god object coupled to all classes of an app." |
| Flyweight | "only when your program must support a huge number of objects which barely fit into available RAM" | "The code becomes much more complicated." |
| Proxy | lazy initialization, access control, remote proxy, caching, logging | "a lot of new classes", delayed responses |
| Chain of Responsibility | "exact types of requests and their sequences are unknown beforehand" | "Some requests may end up unhandled." |
| Command | "parameterize objects with operations"; queue, schedule, undo and redo | "introducing a whole new layer between senders and receivers" |
| Iterator | "collection has a complex data structure under the hood" | "an overkill if your app only works with simple collections." |
| Mediator | "hard to change some of the classes because they are tightly coupled" | "a mediator can evolve into a God Object." |
| Memento | "snapshots of the object's state to be able to restore a previous state" | "might consume lots of RAM if clients create mementos too often" |
| Observer | "changes to the state of one object may require changing other objects, and the actual set of objects is unknown beforehand or changes dynamically" | "Subscribers are notified in random order." Fowler adds that Observer Synchronization makes behavior implicit (<https://martinfowler.com/eaaDev/uiArchs.html>). |
| State | "behaves differently depending on its current state, the number of states is enormous, and the state-specific code changes frequently" | "overkill if a state machine has only a few states or rarely changes." |
| Strategy | "different variants of an algorithm within an object and be able to switch... during runtime" | "If you only have a couple of algorithms and they rarely change, there's no real reason to overcomplicate the program" |
| Template Method | "several classes that contain almost identical algorithms with some minor differences" | "harder to maintain the more steps they have"; may violate Liskov |
| Visitor | "perform an operation on all elements of a complex object structure" | "You need to update all visitors each time a class gets added to or removed from the element hierarchy." |

Interpreter has no refactoring.guru page and the research did not read the GoF book, so its
fits and over-engineering lines are unverified. Norvig's slides state the intent as "Given a
language, interpret sentences" and say macros make it simpler in Lisp or Dylan; Kerievsky has
Replace Implicit Language With Interpreter. Ask before adding one.

Kerievsky's catalog also has the reverse move, Inline Singleton, which confirms Singleton is often
removed.

## Agent Mistakes

- A factory with one product, a strategy with one strategy, or an interface with one implementation
  and no test double. Do the plain call; add the pattern with the second case.
- A Strategy or Command class for one method, when the language has first-class functions.
- A Visitor over a closed set of variants, when a sum type and `match` give exhaustive checks.
- A Singleton for shared state. Pass the dependency in, or use a module.
- A Facade or Mediator that grows into a god object. Its stated cost is exactly that.
- A pattern the codebase has never used, introduced for a single feature.
- Naming a class after a pattern it does not implement, which misleads the next reader.
- Applying Adapter when the service class is yours; change it to match instead.
- Observer where order or timing matters; the order is not guaranteed.

## Examples

Strategy as a function (Python): no class hierarchy for a one-method variation.

```python
from collections.abc import Callable

Discount = Callable[[float], float]

def member(total: float) -> float:
    return total * 0.9

def checkout(total: float, discount: Discount = lambda t: t) -> float:
    return discount(total)

checkout(100.0, member)
```

Visitor as a sum type and `match` (Rust), where adding a variant fails to compile until every
`match` handles it:

```rust
enum Shape {
    Circle(f64),
    Rect(f64, f64),
}

fn area(s: &Shape) -> f64 {
    match s {
        Shape::Circle(r) => std::f64::consts::PI * r * r,
        Shape::Rect(w, h) => w * h,
    }
}
```

A Visitor is still the choice when the element set is open and operations are added by others, or
when the language has no sum types (inferred).
