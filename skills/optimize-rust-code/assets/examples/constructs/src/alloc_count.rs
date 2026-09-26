//! Counting global allocator for allocation assertions in tests.
//! Register it in a binary (not a library) with:
//!
//! ```ignore
//! #[global_allocator]
//! static ALLOC: CountingAlloc = CountingAlloc;
//! ```
//!
//! `realloc` is counted because Vec/String growth goes through it; counting
//! only `alloc` would hide every growth step after the first.
use std::alloc::{GlobalAlloc, Layout, System};
use std::sync::atomic::{AtomicUsize, Ordering::Relaxed};

pub struct CountingAlloc;

static CALLS: AtomicUsize = AtomicUsize::new(0);
static BYTES: AtomicUsize = AtomicUsize::new(0);

// SAFETY: every method forwards to `System` with the caller's arguments
// unchanged; the counters are atomics and never panic or allocate.
unsafe impl GlobalAlloc for CountingAlloc {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        CALLS.fetch_add(1, Relaxed);
        BYTES.fetch_add(layout.size(), Relaxed);
        unsafe { System.alloc(layout) }
    }

    unsafe fn alloc_zeroed(&self, layout: Layout) -> *mut u8 {
        CALLS.fetch_add(1, Relaxed);
        BYTES.fetch_add(layout.size(), Relaxed);
        unsafe { System.alloc_zeroed(layout) }
    }

    unsafe fn realloc(
        &self,
        ptr: *mut u8,
        layout: Layout,
        new_size: usize,
    ) -> *mut u8 {
        CALLS.fetch_add(1, Relaxed);
        BYTES.fetch_add(new_size, Relaxed);
        unsafe { System.realloc(ptr, layout, new_size) }
    }

    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        unsafe { System.dealloc(ptr, layout) }
    }
}

/// Allocation calls (`alloc` + `alloc_zeroed` + `realloc`) and requested
/// bytes performed by `f`. Single-threaded use only: the counters are
/// process-wide.
pub fn measure<R>(f: impl FnOnce() -> R) -> (usize, usize, R) {
    let calls = CALLS.load(Relaxed);
    let bytes = BYTES.load(Relaxed);
    let result = std::hint::black_box(f());
    (
        CALLS.load(Relaxed) - calls,
        BYTES.load(Relaxed) - bytes,
        result,
    )
}
