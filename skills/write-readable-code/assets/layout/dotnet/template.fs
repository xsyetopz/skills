// F# file template: namespace, opens, literals, types with members, then
// internal modules. F# compiles top to bottom, so helpers precede users.
namespace Project.Component

open System

[<AutoOpen>]
module internal Internal =
    [<Literal>]
    let AssemblyConstant = 2

    let helper (value: int) = Math.Abs value

type PublicType() =
    member _.PublicMember() = helper AssemblyConstant
    member internal _.AssemblyMember() = AssemblyConstant
    member private _.PrivateMember() = ()

type internal InternalType() =
    member _.Run() = helper -1
