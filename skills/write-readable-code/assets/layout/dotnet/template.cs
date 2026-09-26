// C# file template: usings, file-scoped namespace, then one main type with
// its members together; internal helpers after the public surface.
using System;

namespace Project.Component;

public static class Constants
{
    public const int PublicValue = 1;
    internal const int AssemblyValue = 2;
}

public sealed class PublicType
{
    private int state;

    public PublicType() => state = Constants.AssemblyValue;

    public int PublicMethod() => PrivateMethod() + Constants.PublicValue;

    internal int AssemblyMethod() => state;

    private int PrivateMethod() => InternalType.Helper(state);
}

// C# has no private top-level types; the narrowest top-level scope is
// internal (or file-local `file` types since C# 11).
internal static class InternalType
{
    internal static int Helper(int value) => Math.Abs(value);
}
