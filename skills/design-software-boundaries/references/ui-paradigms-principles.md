# UI, paradigms, and principles

## Choose UI state flow from platform mechanics

A UI pattern is not a system architecture. Start with rendering lifecycle,
state-restoration needs, binding/reactivity, command/event facilities, and the
number and independence of state writers.

- **MVC:** use when controller/request handling maps naturally to the framework.
  Controllers can become mixed policy; a component with local state is simpler
  for a small screen.
- **MVP:** use when views need a testable imperative presenter. View interfaces
  can mirror every widget; platform UI tests can suffice for rendering behavior.
- **MVVM:** use where binding, observable state, and commands are native.
  Two-way binding can hide writers; prefer one view model per screen to a global
  binding layer.
- **MVI, Flux/Redux, Elm-style:** use when one-way events and explicit state
  transitions solve debugging, replay, or restoration. Reducer/action ceremony
  and broad rerenders cost more than local component state.
- **Component-oriented:** use when composition and local ownership match the
  framework. Lift state only to the nearest common owner when a concrete shared
  consumer needs it.
- **Immediate mode:** use for frame-derived tools or games. Retained lifecycle
  assumptions do not apply; keep authoritative model outside drawing code.

Use host-platform guidance before importing a label. MVVM fits binding-oriented
XAML; reducers fit explicit event/state frameworks; component state fits
component runtimes. Test state transitions and user-visible effects, not
framework internals. Test lifecycle/restoration for retained UI and model
transitions/render invariants for immediate UI.

## RED — DO NOT: use global state for a local dialog

**Deciding condition:** One dialog owns its open state, and no restoration,
cross-screen coordination, or second consumer exists.

```ts
// RED: reducer, action type, store, and subscription for one open flag.
dispatch({ type: "dialog/open" });
```

Why RED:

- the reducer, action, store, and subscription represent no shared state owner;
- a local UI transition now depends on global infrastructure.

## GREEN — DO: keep state with its only owner

```ts
const [open, setOpen] = useState(false);
<button onClick={() => setOpen(true)}>Open</button>
```

Why GREEN:

- no second consumer, restoration requirement, or cross-screen transition
  exists;
- state stays with its only current owner.

Check:

- verify opening and closing affect the dialog and no unrelated view.

## Paradigms change structure, not requirements

- **Procedural:** make ordered transformations explicit for a bounded workflow.
- **Object-oriented:** encapsulate state/invariants when identity and stable
  polymorphism are real; composition is cheaper than inheritance trees.
- **Functional:** isolate pure transforms and immutable values when effects and
  concurrency need local reasoning; do not force large state copies.
- **Declarative:** express constraints, query, or render intent when the engine
  owns execution; understand its evaluation and failure model.
- **Reactive:** model time-varying streams when cancellation, scheduling, and
  backpressure are controlled; a callback/direct call is simpler otherwise.
- **Actor/CSP:** give mutable state one owner or use bounded channels when
  concurrency requires coordination. Verify ordering, limits, cancellation,
  supervision, and external-effect semantics.
- **Data-oriented/ECS:** use contiguous data and systems when profiling shows
  traversal/locality constraints; ordinary domain structures are simpler.
- **Logic/rule-based:** use a maintained engine only when rules are
  independently authored/evaluated; functions or tables are simpler for fixed
  rules.

## Principles are trade-offs

Information hiding, high cohesion/low coupling, separation of concerns, explicit
ownership/lifetime, immutability, command-query separation, and robust failure
boundaries reduce local reasoning cost. DIP means depend on an abstraction only
when a boundary needs one; it does not require an interface per concrete type.
DRY removes duplicated knowledge, not similar syntax: a premature shared helper
couples unrelated change. YAGNI and KISS reject unproven machinery. SOLID,
GRASP, tell-don't-ask, and the law of Demeter are diagnostic lenses, not
class-count rules. Prefer composition to inheritance when variation is not a
stable subtype contract.

For each principle, name the invariant and likely overuse failure. Test
ownership/lifetime with cancellation and teardown, query/command separation with
observable state, and error boundaries with the real failure mode.

Sources: [Android UI
layer](https://developer.android.com/topic/architecture/ui-layer),
[Microsoft
MVVM](https://learn.microsoft.com/en-us/dotnet/architecture/maui/mvvm),
[React state management](https://react.dev/learn/managing-state),
[SEI ATAM][sei-atam].

[sei-atam]: https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/
