//! Constructs that need a third-party crate: FxHashMap (rustc-hash) and
//! rayon parallel iterators. Kept out of `constructs` so the default
//! verification and smoke runs stay dependency-free.
use rayon::prelude::*;
use rustc_hash::FxHashMap;
use std::collections::HashMap;

// --- FxHashMap for trusted integer keys -----------------------------------

pub fn histogram_std(keys: &[u32]) -> HashMap<u32, u32> {
    let mut counts = HashMap::with_capacity(keys.len());
    for &key in keys {
        *counts.entry(key).or_insert(0) += 1;
    }
    counts
}

pub fn histogram_fx(keys: &[u32]) -> FxHashMap<u32, u32> {
    let mut counts =
        FxHashMap::with_capacity_and_hasher(keys.len(), Default::default());
    for &key in keys {
        *counts.entry(key).or_insert(0) += 1;
    }
    counts
}

// --- rayon par_iter for independent CPU-bound items ------------------------

/// Deliberately CPU-heavy per item so the work outweighs task overhead.
pub fn collatz_steps(mut n: u64) -> u32 {
    let mut steps = 0;
    while n > 1 {
        n = if n % 2 == 0 { n / 2 } else { 3 * n + 1 };
        steps += 1;
    }
    steps
}

pub fn steps_serial(inputs: &[u64]) -> Vec<u32> {
    inputs.iter().map(|&n| collatz_steps(n)).collect()
}

pub fn steps_parallel(inputs: &[u64]) -> Vec<u32> {
    inputs.par_iter().map(|&n| collatz_steps(n)).collect()
}

pub fn max_serial(inputs: &[u64]) -> Option<u32> {
    inputs.iter().map(|&n| collatz_steps(n)).max()
}

pub fn max_parallel(inputs: &[u64]) -> Option<u32> {
    inputs.par_iter().map(|&n| collatz_steps(n)).max()
}
