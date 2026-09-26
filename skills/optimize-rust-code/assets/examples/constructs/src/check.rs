//! Oracle helpers. A failed check panics, so `constructs verify` exits
//! nonzero and names the construct.
use crate::alloc_count;
use std::fmt::Debug;
use std::sync::atomic::{AtomicUsize, Ordering::Relaxed};

static CHECKS: AtomicUsize = AtomicUsize::new(0);

pub fn count() -> usize {
    CHECKS.load(Relaxed)
}

pub fn equal<T: PartialEq + Debug>(name: &str, expected: T, actual: T) {
    CHECKS.fetch_add(1, Relaxed);
    assert!(
        expected == actual,
        "{name}: expected {expected:?}, got {actual:?}"
    );
}

/// Allocation calls of `f` on its second run (the first run warms lazy
/// statics and thread-locals).
pub fn allocations<R>(mut f: impl FnMut() -> R) -> usize {
    std::hint::black_box(f());
    alloc_count::measure(f).0
}

/// Asserts the baseline allocates and the candidate allocates strictly
/// less; a zero-allocation baseline would make the check vacuous.
pub fn fewer_allocations<A, B>(
    name: &str,
    baseline: impl FnMut() -> A,
    candidate: impl FnMut() -> B,
) {
    CHECKS.fetch_add(1, Relaxed);
    let before = allocations(baseline);
    let after = allocations(candidate);
    println!("ALLOC {name}: {before} -> {after} allocation calls");
    assert!(before > 0, "{name}: baseline did not allocate; vacuous");
    assert!(after < before, "{name}: {after} is not below {before}");
}

/// Asserts a counted quantity (writes, reads, hashes) strictly decreased.
pub fn fewer(name: &str, what: &str, before: usize, after: usize) {
    CHECKS.fetch_add(1, Relaxed);
    println!("COUNT {name}: {before} -> {after} {what}");
    assert!(before > 0, "{name}: baseline count is zero; vacuous");
    assert!(after < before, "{name}: {after} is not below {before}");
}
