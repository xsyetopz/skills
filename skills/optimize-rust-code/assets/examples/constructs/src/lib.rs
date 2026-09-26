//! Construct catalog: each module holds baseline/candidate pairs that are
//! observably equivalent. `main.rs` registers the counting allocator and
//! runs the oracles (`verify`), a one-shot smoke run (`smoke`), or the
//! std-only timing harness (`time`).
pub mod alloc_count;
pub mod allocation;
pub mod check;
pub mod codegen;
pub mod collections;
pub mod dispatch;
pub mod harness;
pub mod io;
