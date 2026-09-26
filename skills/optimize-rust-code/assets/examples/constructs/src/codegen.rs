//! Code-generation constructs. `#[unsafe(no_mangle)]` keeps stable symbol
//! names so `verify.sh asm` can find each function in the emitted assembly
//! and count bounds-check panics, indirect calls, and vector instructions.

// --- iterators instead of indexing ---------------------------------------

/// Panics if `b` is shorter than `a` (bounds check on `b[i]`).
#[unsafe(no_mangle)]
pub fn dot_index_baseline(a: &[u32], b: &[u32]) -> u32 {
    let mut sum = 0u32;
    for i in 0..a.len() {
        sum = sum.wrapping_add(a[i].wrapping_mul(b[i]));
    }
    sum
}

/// Same panic contract, checked once; the loop has no bounds checks.
#[unsafe(no_mangle)]
pub fn dot_iter_candidate(a: &[u32], b: &[u32]) -> u32 {
    assert!(b.len() >= a.len(), "b shorter than a");
    a.iter()
        .zip(b)
        .fold(0u32, |sum, (&x, &y)| sum.wrapping_add(x.wrapping_mul(y)))
}

// --- reslice before the loop ---------------------------------------------

/// Adds `src[i]` into `dst[i]` for every index of `dst`.
#[unsafe(no_mangle)]
pub fn add_index_baseline(dst: &mut [u32], src: &[u32]) {
    for i in 0..dst.len() {
        dst[i] = dst[i].wrapping_add(src[i]);
    }
}

#[unsafe(no_mangle)]
pub fn add_reslice_candidate(dst: &mut [u32], src: &[u32]) {
    // One length check (panics like the baseline when src is too short);
    // afterwards LLVM knows i < dst.len() == src.len().
    let src = &src[..dst.len()];
    for i in 0..dst.len() {
        dst[i] = dst[i].wrapping_add(src[i]);
    }
}

// --- chunks_exact ---------------------------------------------------------

/// Sum of little-endian u32 words; a trailing partial word is ignored.
#[unsafe(no_mangle)]
pub fn words_index_baseline(bytes: &[u8]) -> u32 {
    let mut sum = 0u32;
    let mut i = 0;
    while i + 4 <= bytes.len() {
        let word = u32::from_le_bytes([
            bytes[i],
            bytes[i + 1],
            bytes[i + 2],
            bytes[i + 3],
        ]);
        sum = sum.wrapping_add(word);
        i += 4;
    }
    sum
}

#[unsafe(no_mangle)]
pub fn words_chunks_candidate(bytes: &[u8]) -> u32 {
    bytes.chunks_exact(4).fold(0u32, |sum, chunk| {
        let word = u32::from_le_bytes(chunk.try_into().expect("len 4"));
        sum.wrapping_add(word)
    })
}

// --- get_unchecked behind a checked invariant -----------------------------

/// Indices validated once at construction; the hot loop relies on that.
pub struct Gather {
    indices: Vec<usize>,
    source_len: usize,
}

impl Gather {
    pub fn new(indices: Vec<usize>, source_len: usize) -> Option<Self> {
        if indices.iter().all(|&i| i < source_len) {
            Some(Self {
                indices,
                source_len,
            })
        } else {
            None
        }
    }
}

#[unsafe(no_mangle)]
pub fn gather_checked_baseline(plan: &Gather, data: &[u32]) -> u32 {
    assert_eq!(data.len(), plan.source_len, "data length changed");
    plan.indices
        .iter()
        .fold(0u32, |sum, &i| sum.wrapping_add(data[i]))
}

#[unsafe(no_mangle)]
pub fn gather_unchecked_candidate(plan: &Gather, data: &[u32]) -> u32 {
    assert_eq!(data.len(), plan.source_len, "data length changed");
    plan.indices.iter().fold(0u32, |sum, &i| {
        // PERF/SAFETY: `Gather::new` proved every index < source_len, the
        // fields are private and immutable after construction, and the
        // assert above proves data.len() == source_len, so i < data.len().
        sum.wrapping_add(unsafe { *data.get_unchecked(i) })
    })
}

// --- auto-vectorization of a float reduction -----------------------------

/// One serial chain of dependent adds: LLVM must keep IEEE evaluation
/// order, so it cannot split the sum across vector lanes.
#[unsafe(no_mangle)]
pub fn sum_f32_baseline(values: &[f32]) -> f32 {
    values.iter().sum()
}

/// Eight independent partial sums: each lane is its own dependency chain,
/// which LLVM maps onto vector registers. The rounding order changes, so
/// results are bit-identical only when every partial sum is exact.
#[unsafe(no_mangle)]
pub fn sum_f32_candidate(values: &[f32]) -> f32 {
    // -0.0 is the exact additive identity and what `Sum` returns for an
    // empty iterator; starting lanes at 0.0 would turn -0.0 into 0.0.
    let mut lanes = [-0.0f32; 8];
    let chunks = values.chunks_exact(8);
    let tail = chunks.remainder();
    for chunk in chunks {
        for (lane, &value) in lanes.iter_mut().zip(chunk) {
            *lane += value;
        }
    }
    lanes.iter().sum::<f32>() + tail.iter().sum::<f32>()
}

// --- #[inline] across crates ---------------------------------------------

#[unsafe(no_mangle)]
pub fn scale_all_baseline(values: &[u32]) -> u32 {
    values
        .iter()
        .fold(0u32, |sum, &v| sum.wrapping_add(helper::scale(v)))
}

#[unsafe(no_mangle)]
pub fn scale_all_candidate(values: &[u32]) -> u32 {
    values
        .iter()
        .fold(0u32, |sum, &v| sum.wrapping_add(helper::scale_inline(v)))
}

// --- sort_unstable ---------------------------------------------------------

pub fn sort_baseline(values: &mut [u32]) {
    values.sort();
}

pub fn sort_candidate(values: &mut [u32]) {
    // Equal u32 values are indistinguishable, so stability is unobservable.
    values.sort_unstable();
}

// --- memchr-backed std search ---------------------------------------------

/// Splits "key:value" at the first ':'.
pub fn split_key_baseline(line: &str) -> Option<(&str, &str)> {
    for (i, c) in line.char_indices() {
        if c == ':' {
            return Some((&line[..i], &line[i + 1..]));
        }
    }
    None
}

pub fn split_key_candidate(line: &str) -> Option<(&str, &str)> {
    line.split_once(':')
}

pub fn has_newline_baseline(bytes: &[u8]) -> bool {
    bytes.iter().any(|&b| b == b'\n')
}

pub fn has_newline_candidate(bytes: &[u8]) -> bool {
    bytes.contains(&b'\n')
}

// --- #[target_feature] with runtime detection -----------------------------

pub fn sum_u32_portable(values: &[u32]) -> u32 {
    values.iter().fold(0u32, |sum, &v| sum.wrapping_add(v))
}

/// Compiled with AVX2 enabled for this function only (Rust 1.86+ allows
/// a safe fn here; callers without the feature still need `unsafe`).
#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
fn sum_u32_avx2(values: &[u32]) -> u32 {
    values.iter().fold(0u32, |sum, &v| sum.wrapping_add(v))
}

/// One binary for every x86_64 CPU: AVX2 path only where detected.
pub fn sum_u32_dispatch(values: &[u32]) -> u32 {
    #[cfg(target_arch = "x86_64")]
    if std::arch::is_x86_feature_detected!("avx2") {
        // PERF/SAFETY: the running CPU reported AVX2 just above.
        return unsafe { sum_u32_avx2(values) };
    }
    sum_u32_portable(values)
}
