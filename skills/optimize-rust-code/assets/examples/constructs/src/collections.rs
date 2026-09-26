//! Collection constructs. `CountingState` counts hash computations so the
//! entry-API card has a deterministic benefit oracle.
use std::cell::Cell;
use std::collections::HashMap;
use std::collections::hash_map::RandomState;
use std::hash::{BuildHasher, Hasher};
use std::rc::Rc;

/// Wraps std's `RandomState` and counts every `finish()` (one per hash).
#[derive(Clone, Default)]
pub struct CountingState {
    inner: RandomState,
    pub hashes: Rc<Cell<usize>>,
}

pub struct CountingHasher<H> {
    inner: H,
    hashes: Rc<Cell<usize>>,
}

impl BuildHasher for CountingState {
    type Hasher = CountingHasher<<RandomState as BuildHasher>::Hasher>;
    fn build_hasher(&self) -> Self::Hasher {
        CountingHasher {
            inner: self.inner.build_hasher(),
            hashes: Rc::clone(&self.hashes),
        }
    }
}

impl<H: Hasher> Hasher for CountingHasher<H> {
    fn finish(&self) -> u64 {
        self.hashes.set(self.hashes.get() + 1);
        self.inner.finish()
    }
    fn write(&mut self, bytes: &[u8]) {
        self.inner.write(bytes);
    }
}

pub type Counts<'a, S> = HashMap<&'a str, usize, S>;

// --- entry API instead of contains_key + insert --------------------------

pub fn count_words_baseline<'a, S: BuildHasher>(
    counts: &mut Counts<'a, S>,
    text: &'a str,
) {
    for word in text.split_whitespace() {
        if counts.contains_key(word) {
            *counts.get_mut(word).expect("checked above") += 1;
        } else {
            counts.insert(word, 1);
        }
    }
}

pub fn count_words_candidate<'a, S: BuildHasher>(
    counts: &mut Counts<'a, S>,
    text: &'a str,
) {
    for word in text.split_whitespace() {
        *counts.entry(word).or_insert(0) += 1;
    }
}

// --- HashMap::with_capacity ------------------------------------------------

pub fn index_baseline(keys: &[u32]) -> HashMap<u32, usize> {
    let mut map = HashMap::new();
    for (i, &key) in keys.iter().enumerate() {
        map.insert(key, i);
    }
    map
}

pub fn index_candidate(keys: &[u32]) -> HashMap<u32, usize> {
    let mut map = HashMap::with_capacity(keys.len());
    for (i, &key) in keys.iter().enumerate() {
        map.insert(key, i);
    }
    map
}
