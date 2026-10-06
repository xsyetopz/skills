# C# and F#

## C# files

Visibility, narrowest first: `private`, `file` (top-level types, C# 11), `internal`,
`protected`, `public`.
A top-level helper type that only this file uses is `file`, not `internal`.
Use a file-scoped namespace.
Implicit usings are on in current SDK projects, so do not add `using System;` by hand.

1. File-scoped `namespace`, after the `using` directives.
1. The main type, with its members together.
1. Inside the type: constants and static fields, instance fields, constructors, properties,
   public methods, `internal` methods, `protected` methods, `private` methods, nested types.
1. Supporting `internal` types.
1. `file` types last.

Never split a type from its members to group by visibility.
Tests go in a separate test project (`Project.Tests`).
Use `InternalsVisibleTo` only when an existing test project needs `internal` access.

```csharp
using Project.Other;

namespace Project.Component;

public sealed class PublicType
{
    public const int PublicValue = 1;
    private const int PrivateValue = 2;

    private int _state = PrivateValue;

    public PublicType() { }

    public void PublicMethod() => Helper.Run(_state);

    internal void AssemblyMethod() { }

    private void PrivateMethod() { }
}

internal sealed class InternalType
{
    internal void Run() { }
}

file static class Helper
{
    internal static void Run(int state) { }
}
```

## F# files

F# has no `protected`.
Use `private` and `internal`,
and a signature file (`.fsi`) when a module's public surface must be explicit.
File order in the project is dependency order,
and inside a file a declaration comes before its use,
so place helpers before the code that calls them.
This is the one exception to "main type first".
A `[<Literal>]` is a `let` binding and needs a module, not a bare namespace.

1. `namespace` or top-level `module`.
1. `open` declarations.
1. Module with constants.
1. Private helpers, before their callers.
1. Types, each followed by its members.
1. Public functions in a module.

```fsharp
namespace Project.Component

open Project.Other

module Constants =
    [<Literal>]
    let PublicConstant = 1

module private Helpers =
    let run (state: int) = state + Constants.PublicConstant

type PublicType() =
    member _.PublicMember() = Helpers.run 0
    member internal _.AssemblyMember() = ()
    member private _.PrivateMember() = ()

type internal InternalType() =
    member _.Run() = ()
```
