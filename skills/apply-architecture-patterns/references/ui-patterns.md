# UI Patterns

Read when the code is MVC, MVP, or MVVM, or when you must decide whether logic belongs in a view,
controller, presenter, or view model.

## Contents

- [The Shared Rule](#the-shared-rule)
- [Recognize the Pattern](#recognize-the-pattern)
- [Where Logic Goes](#where-logic-goes)
- [Platform Notes](#platform-notes)
- [Agent Mistakes](#agent-mistakes)
- [Example](#example)

## The Shared Rule

Every variant separates presentation from domain logic. Fowler: MVC is "a set of principles
including the separation of presentation from domain logic and synchronizing presentation state
through events." <https://martinfowler.com/eaaDev/uiArchs.html>

His worked example: "Calculating the variance between actual and target is domain behavior, it is
nothing to do with the UI... we should place this in the domain layer". Reenskaug's 1979 note puts
it briefly: "Models represent knowledge." The Smalltalk-80 Controller was used differently from the
original note, so do not assume a textbook Controller from the name.
<https://folk.universitetetioslo.no/trygver/themes/mvc/mvc-index.html>

In clean architecture, "The Presenters, Views, and Controllers all belong" in the interface adapter
layer, so none of them holds business rules (see `ports-and-layers.md`).

## Recognize the Pattern

Decide from who knows whom, not from class names. A `ViewModel` suffix does not make code MVVM.

| Pattern | Evidence in code |
| --- | --- |
| MVC | Controller receives input, picks a model operation and a view. Views read or observe the model. |
| MVP | A presenter holds a reference to a view interface and pushes data into it. The view is thin. |
| MVVM | The view binds to a view model; the view model does not reference the view. |

MVP variants differ in how the view updates ("Different variants of MVP handle view updates
differently", Fowler). In Passive View the presenter "also handles the population of data in the UI
widgets". In Supervising Controller "the view handles simple mapping to the underlying model and
the controller handles input response and complex view logic."
<https://martinfowler.com/eaaDev/SupervisingPresenter.html>. Humble View's rule: "any object that is
difficult to test should have minimal behavior."

MVVM is Fowler's Presentation Model, "a model that is really designed for and thus part of the
presentation layer. (It's also known as MVVM...)". It holds presentation state (selection, whether
the save button is enabled) and UI-only logic such as text colour.

Microsoft's MVVM dependency rule: "the view 'knows about' the view model, and the view model 'knows
about' the model, but the model is unaware of the view model, and the view model is unaware of the
view." <https://learn.microsoft.com/en-us/dotnet/architecture/maui/mvvm>

Check the nearest screen: what does its view reference, what does its view model or presenter
import, and where do its tests live.

## Where Logic Goes

| Logic | Owner |
| --- | --- |
| Business rules, calculations, validation that is a domain rule | Domain or data layer, called by a use case |
| Which fields are enabled, selection, formatting, text colour | Presentation model, view model, or presenter |
| Mapping a model value to widget properties | View (MVVM binding, Supervising Controller) or presenter (Passive View) |
| Parsing input, calling one use case, mapping the result | Controller or presenter |
| Navigation, resources, messages | UI layer (Android: "how to display state") |

Android states the line directly: "Business logic is usually placed in the domain or data layers,
but never in the UI layer." <https://developer.android.com/topic/architecture/ui-layer>. Its guide
asks for at least a UI layer and a data layer that "contains the business logic", with an optional
domain layer, a "single source of truth", and unidirectional data flow.
<https://developer.android.com/topic/architecture>. The domain layer is "responsible for
encapsulating complex business logic, or simple business logic that is reused by multiple
ViewModels." <https://developer.android.com/topic/architecture/domain-layer>

## Platform Notes

- .NET MAUI: "In MVVM, a model is ignorant of the viewmodel, and a viewmodel is ignorant of the
  view." <https://learn.microsoft.com/en-us/dotnet/maui/xaml/fundamentals/mvvm?view=net-maui-9.0>
- SwiftUI: apply the `@Observable` macro to the model type, and "always use the `Observable` macro"
  rather than the protocol alone. The page keeps the data model separate from views but does not
  define a domain layer, so put rules where the codebase's existing model layer puts them.
  <https://developer.apple.com/documentation/swiftui/managing-model-data-in-your-app>

## Agent Mistakes

- Pricing, permission, or validation rules in a controller action, click handler, or view body.
  Move them to a domain type or use case and call that from the screen.
- A view model that opens a database connection, calls HTTP directly, or imports a view type. The
  view model depends on the model or a use case only.
- A presenter or view model that holds a reference to a concrete view, in a codebase that binds
  instead. Match the existing wiring.
- Mixing patterns in one screen: a presenter plus a binding layer, or a view model that behaves as a
  controller. Copy the nearest screen.
- Adding a domain layer, use case class, or mapper to a small screen when sibling screens call the
  data layer directly. Android calls the domain layer optional; follow the codebase.
- Putting formatting in the domain to make the view simpler. Presentation concerns stay in
  presentation.
- Using Observer wiring where an explicit call would do. Fowler notes Observer Synchronization
  makes behavior implicit.

## Example

An MVVM view model: presentation state and UI-only logic here, the rule in the domain (Kotlin
sketch, names illustrative):

```kotlin
// domain: owns the rule
class Order(val lines: List<Line>) {
    fun total(): Money = lines.sumOf { it.price * it.qty }
    fun canSubmit(): Boolean = lines.isNotEmpty()
}

// view model: presentation state, no view reference, no database client
class OrderViewModel(private val submitOrder: SubmitOrder) : ViewModel() {
    val state = MutableStateFlow(OrderUiState())

    fun onSubmitClicked(order: Order) {
        state.update {
            it.copy(submitEnabled = order.canSubmit(), totalText = order.total().format())
        }
        if (order.canSubmit()) viewModelScope.launch { submitOrder(order) }
    }
}
```

The view renders `state` and forwards clicks. It computes nothing about money or validity.
