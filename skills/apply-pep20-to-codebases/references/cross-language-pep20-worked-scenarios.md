# Worked scenarios for Cross Language PEP 20

## Rust: make ownership explicit without adding wrappers

Ambiguous:

```rust
fn load(path: &str) -> Vec<u8> { /* panics, reads global cache */ }
```

A better contract may be:

```rust
fn load(path: &Path, cache: &mut Cache) -> io::Result<Arc<[u8]>> {
    cache.get_or_read(path)
}
```

The improvement is not “Rust that looks like Python.” The dependencies, error,
path type, and shared ownership are now visible. Retain `Arc` only when shared
ownership is real; otherwise return owned bytes or a borrow.

## C#: one resource lifetime, one canonical path

```csharp
public async Task<Payload> ReadAsync(Stream source, CancellationToken ct)
{
    ArgumentNullException.ThrowIfNull(source);
    return await parser.ReadAsync(source, ct).ConfigureAwait(false);
}
```

Do not add a second overload that silently creates a stream, swallows errors,
and ignores cancellation merely for “convenience.” A convenience API is valid
when its ownership and failure behavior are explicit and a real consumer needs
it.

## Go: name units and failure behavior

```go
type Timeout struct {
    Request time.Duration
    Idle    time.Duration
}

func ReadFrame(r io.Reader, maxBytes int) ([]byte, error)
```

`timeout`, `size`, and `doThing` hide units and intent. The revised names make
constraints explicit without verbose prose at every call site.

## C++: retain justified abstraction

A virtual interface used by production, simulator, and hardware-backed drivers
is not “unnecessary indirection” merely because one build selects one driver.
Review ownership, ABI, test substitution, and deployment boundaries. PEP 20
supports removing accidental complexity, not denying genuine variation.
