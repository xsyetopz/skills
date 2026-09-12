# .NET memory and native boundaries

## Optimize semantics, not spelling

Prefer eliminating repeated work and unnecessary materialization over replacing
every LINQ expression, delegate or interface. Preserve deferred execution,
enumeration count, exception timing, ordering and comparer semantics where they
are observable. Modern JITs can specialize familiar patterns; verify the
selected runtime's code generation before assuming an abstraction allocates or
dispatches.

Do not replace `value.HasFlag(mask)` with `(value & mask) != 0`
indiscriminately. For values of the same enum type, `HasFlag` tests whether
**all** mask bits are present, including a true result for a zero mask. The
nonzero expression instead tests whether **any** bit is present. Test composite
and zero masks when touching permission or feature checks. [HasFlag
contract][flags].

Use standard span-based APIs when a view avoids an identified copy. Preserve
culture, encoding and malformed-input behavior; a span rewrite is not permission
to invent a reduced parser or serializer. Check the target framework and
compiler before choosing new overloads. [Memory and spans][spans].

## Borrowed and pooled storage

For `CollectionsMarshal.AsSpan(list)`, prevent adding or removing list elements
while the view is in use, including through aliases and callbacks. A view is not
a synchronization primitive. Prefer ordinary collection APIs when exclusive
ownership cannot be established. [AsSpan contract][as-span].

An `ArrayPool<T>` rental may be larger than requested and contain previous data.
Use the logical initialized slice, return it to the same pool exactly once after
all consumers finish, and never access it after return. Use `finally` for the
ownership scope. Clear sensitive used contents before relinquishing ownership;
consider reference retention as well as confidentiality. Do not return an array
while an asynchronous write still consumes its memory. [Rent][rent],
[Return][return].

Pooling adds retention, lifetime and reset costs. Measure it against direct
allocation for the real size distribution. A bounded stack buffer may avoid a
rental, but do not size `stackalloc` from unbounded external input or allocate
it repeatedly inside a long loop. Initialize every element before reading it.
[Unsafe-code guidance][unsafe].

## Unsafe and native operations

Require a measured reason and an explicit invariant before bypassing safe APIs:
bounds, initialization, alignment, overlap, aliasing, object lifetime and GC
movement. Managed references track relocation; raw pointers do not. Keep
pointers to movable managed storage within the appropriate pinning lifetime. A
nearby comment or passing test cannot prove this contract, and the absence of an
`unsafe` block does not make `Unsafe` APIs safe. Prefer safe span operations
when they achieve the same result. [Unsafe-code guidance][unsafe].

Match the actual native header and platform ABI: integer widths, Boolean and
string representation, struct layout, calling convention, ownership and error
reporting. A C library's documentation does not prove a particular C# wrapper's
API shape. Inspect the selected binding version and native library together. Use
maintained bindings or supported generated interop rather than a new wrapper
layer by default. [Interop guidance][interop].

Where supported, evaluate `LibraryImport` for source-generated marshalling.
Prefer `SafeHandle` for owned native handles. Root callback delegates for the
entire native registration, coordinate unregistering with in-flight callbacks,
and do not release buffers while native code still uses them. Boundaries must
translate errors without letting managed exceptions escape into unmanaged code.
Pinning a buffer does not extend the logical operation or registration lifetime.
[Interop guidance][interop].

Measure wrapper overhead separately from the native operation when possible. Do
not trade correctness for lower reported allocation: unmanaged leaks and
long-lived pins may disappear from a managed bytes-per-operation result. SIMD,
unsafe and native changes need target-specific validation, including supported
CPU features and a portable path where the deployment requires one.

[flags]: https://learn.microsoft.com/en-us/dotnet/api/system.enum.hasflag
[spans]: https://learn.microsoft.com/en-us/dotnet/standard/memory-and-spans/
[as-span]:
  https://learn.microsoft.com/en-us/dotnet/api/system.runtime.interopservices.collectionsmarshal.asspan
[rent]:
  https://learn.microsoft.com/en-us/dotnet/api/system.buffers.arraypool-1.rent
[return]:
  https://learn.microsoft.com/en-us/dotnet/api/system.buffers.arraypool-1.return
[unsafe]:
  https://learn.microsoft.com/en-us/dotnet/standard/unsafe-code/best-practices
[interop]:
  https://learn.microsoft.com/en-us/dotnet/standard/native-interop/best-practices
