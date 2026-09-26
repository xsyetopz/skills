# String building

## strings.Builder instead of += in loops

**Definition.** Concatenating with `+=` in a loop copies the whole string
each iteration; `strings.Builder` grows one buffer.

**Example.** `assets/concat/concat_test.go` has `BenchmarkPlus` and
`BenchmarkBuilder` over 1,000 short strings.

**Cost removed.** TODO: ns/op and allocs/op before and after.

## Preallocate with Grow

**Definition.** `b.Grow(n)` reserves the final size once when it is known.

**Cost removed.** TODO: allocs/op with and without Grow.
