# Verify .NET unsafe code and native-library interfaces

## Prove the boundary before optimizing it

Read the exact installed binding and native API version. Identify the actual
implementation boundary: managed port, native library, generated P/Invoke, or
callback. StbImageSharp is a managed C# port of stb_image, not inherently a
native P/Invoke wrapper. FontStashSharp is also a C# port; optional
font/rasterization backends can introduce separate native boundaries. Do not
translate C ownership rules to a similarly named C# package without inspecting
its implementation.

For Hexa.NET.SDL3, ManagedBass/ManagedBass.Fx, and related bindings, verify the
current method signatures, threading rules, handle lifetime, and native binary
identity. Attribute native execution separately from marshaling and managed
allocation. A managed profiler's inclusive native call does not reveal the
native internal bottleneck by itself.

## Required reasoning for a risky change

State the valid index range and prove address arithmetic cannot overflow it.
Establish alignment, element representation, object lifetime, aliasing,
concurrent access, and the owner that keeps memory valid. Show the behavior for
zero length and boundary inputs. A `PERF/SAFETY` comment documents the argument;
neither comment presence nor a source grep establishes it.

Prefer supported safe primitives such as span slicing/copying when they meet the
measured goal. Use `Unsafe`, `MemoryMarshal`, pointers, or manual bounds-check
elimination only for a demonstrated cost and a specific invariant. Keep
`stackalloc` sizes bounded; do not allow attacker-controlled size or accumulate
repeated stack allocations in a long-running loop. Preserve a supported non-SIMD
path where the deployment requires it.

## Interop ownership and callbacks

Match ABI types, field layout/packing, calling convention, string encoding, bool
representation, and error signaling to the native declaration. A C `long` does
not have the same size on every ABI. Use an appropriate SafeHandle-based
ownership pattern for owned handles unless the API's lifetime rules require
something else. Distinguish owned from borrowed handles.

Root a delegate for the entire period native code may call it, not merely until
registration returns. Unregister and wait for in-flight callbacks to quiesce
according to the native contract before releasing callback state or library
resources. Do not let managed exceptions escape across an unmanaged callback
boundary; translate/report them through a defined mechanism. Do not silently
swallow a failure and claim the callback succeeded.

For audio/render paths, establish the actual callback thread and deadline. Avoid
blocking, allocation, synchronous logging, and heavy work on a deadline-bound
audio callback; move work across a bounded ownership-safe handoff. Do not invent
a lock-free ring without proving its producer/consumer model and memory
ordering.

Pin only for the required native use, or use owned unmanaged memory when the
native lifetime requires it and cleanup is explicit. Do not free or return a
buffer while native asynchronous work still holds its address. Test
cancellation, registration failure, teardown races, and exceptional cleanup, not
only the successful hot loop.

Sources: [Microsoft native interop
guidance][ref-microsoft-native-interop-guidance],
[StbImageSharp][ref-stbimagesharp], [FontStashSharp][ref-fontstashsharp], [SDL3
API](https://wiki.libsdl.org/SDL3/CategoryAPI), [BASS
documentation](https://www.un4seen.com/doc/).

## SDL3, font/text, image and audio workloads

For SDL3, keep event pumping and renderer API calls on the documented main
thread. `SDL_PollEvent`, `SDL_RenderGeometry` and `SDL_RenderPresent` return
bool in SDL3; do not copy SDL2 signatures or reinterpret success as the old
integer convention. `SDL_RenderGeometry` uses per-vertex color/alpha modulation,
not the texture modulation setters. Check errors from the actual binding/native
return.

Do not claim a whole frame is GPU time because `RenderPresent` blocks: capture
CPU submission, driver wait and GPU measurements at their actual boundaries.
SDL's backbuffer contents are not preserved by contract after presentation. A
cache of renderer state must be invalidated whenever another owner can change
that state; skipping setters blindly can alter output. Batching must preserve
ordering where blending or depth makes it observable.

For FontStashSharp/fontstash, identify the actual rasterizer and renderer
backend. Cache glyphs/layout only with a key covering font identity, size,
scale, content, layout/shaping and style as appropriate to the selected API. A
glyph atlas is not a complete shaping implementation. Test atlas growth, missing
glyphs, Unicode, resize and graphics-resource teardown; do not preload an
unbounded character space merely to avoid one first-use stall.

For image decode/upload, distinguish compressed input, decoded pixel format,
stride, orientation, staging storage and GPU ownership. Do not assume a managed
port can decode into caller-provided storage without that API. Validate size
arithmetic before allocation; reject unsupported format/depth explicitly. Keep
resource disposal after the last real consumer, not merely after submission.

For BASS/ManagedBass and FX, verify the native version, callback kind and handle
ownership in the selected package and official BASS documentation. Keep callback
work bounded and avoid blocking, allocation and synchronous logging when the
callback deadline forbids them. Reuse analysis buffers only when no consumer
retains a previous result. A ring buffer requires explicit
single-/multi-producer semantics, capacity/full behavior and memory ordering;
calling it lock-free is not a proof. Measure underruns, callback deadlines and
device buffering separately from UI/render throughput. Never release callback
state until unregister and quiescence are established by the actual native
contract.

Additional API sources: [SDL3 event polling][sdl-poll-event],
[SDL_RenderGeometry][upstream-source-1], [SDL_RenderPresent][upstream-source-2],
[FontStashSharp binding][upstream-source-3], [StbImageSharp
binding][upstream-source-4], [BASS library reference][upstream-source-5]

[ref-microsoft-native-interop-guidance]: https://learn.microsoft.com/en-us/dotnet/standard/native-interop/best-practices
[ref-stbimagesharp]: https://github.com/StbSharp/StbImageSharp
[ref-fontstashsharp]: https://github.com/FontStashSharp/FontStashSharp

[upstream-source-1]: https://wiki.libsdl.org/SDL3/SDL_RenderGeometry
[upstream-source-2]: https://wiki.libsdl.org/SDL3/SDL_RenderPresent
[upstream-source-3]: https://github.com/FontStashSharp/FontStashSharp
[upstream-source-4]: https://github.com/StbSharp/StbImageSharp
[upstream-source-5]: https://www.un4seen.com/doc/

[sdl-poll-event]: https://wiki.libsdl.org/SDL3/SDL_PollEvent
