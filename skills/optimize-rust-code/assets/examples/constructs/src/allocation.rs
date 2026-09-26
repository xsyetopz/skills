//! Allocation constructs: each pair returns the same value; the oracle in
//! `main.rs` proves equality and that the candidate allocates less.
use std::borrow::Cow;
use std::fmt::Write as _;
use std::rc::Rc;
use std::sync::Arc;

// --- Vec::with_capacity -------------------------------------------------

pub fn squares_baseline(n: u64) -> Vec<u64> {
    let mut out = Vec::new();
    for i in 0..n {
        out.push(i * i);
    }
    out
}

pub fn squares_candidate(n: u64) -> Vec<u64> {
    let len = usize::try_from(n).expect("n fits in usize");
    let mut out = Vec::with_capacity(len);
    for i in 0..n {
        out.push(i * i);
    }
    out
}

// --- reserve + extend_from_slice -----------------------------------------

pub fn flatten_baseline(batches: &[Vec<u32>]) -> Vec<u32> {
    let mut out = Vec::new();
    for batch in batches {
        for &value in batch {
            out.push(value);
        }
    }
    out
}

pub fn flatten_candidate(batches: &[Vec<u32>]) -> Vec<u32> {
    let total = batches.iter().map(Vec::len).sum();
    let mut out = Vec::new();
    out.reserve_exact(total);
    for batch in batches {
        out.extend_from_slice(batch);
    }
    out
}

// --- reuse a scratch buffer with clear() ---------------------------------

/// Longest line measured in whitespace-separated fields.
pub fn widest_baseline(text: &str) -> usize {
    let mut widest = 0;
    for line in text.lines() {
        let fields: Vec<&str> = line.split_whitespace().collect();
        widest = widest.max(fields.len());
    }
    widest
}

pub fn widest_candidate(text: &str) -> usize {
    let mut widest = 0;
    let mut fields: Vec<&str> = Vec::new();
    for line in text.lines() {
        fields.clear(); // keeps capacity from earlier lines
        fields.extend(line.split_whitespace());
        widest = widest.max(fields.len());
    }
    widest
}

// --- borrowed parameters instead of owned ones ---------------------------

pub fn admins_baseline(names: Vec<String>) -> usize {
    names
        .iter()
        .filter(|name| name.starts_with("admin"))
        .count()
}

pub fn admins_candidate(names: &[String]) -> usize {
    names
        .iter()
        .filter(|name| name.starts_with("admin"))
        .count()
}

// --- clone_from reuses the destination allocation ------------------------

pub fn snapshots_baseline(frames: &[Vec<u8>]) -> usize {
    let mut last = Vec::new();
    let mut total = 0;
    for frame in frames {
        last = frame.clone();
        total += last.len();
    }
    total + last.len()
}

pub fn snapshots_candidate(frames: &[Vec<u8>]) -> usize {
    let mut last = Vec::new();
    let mut total = 0;
    for frame in frames {
        last.clone_from(frame);
        total += last.len();
    }
    total + last.len()
}

// --- Cow: allocate only when the input must change -----------------------

pub fn detab_baseline(line: &str) -> String {
    line.replace('\t', "    ")
}

pub fn detab_candidate(line: &str) -> Cow<'_, str> {
    if line.contains('\t') {
        Cow::Owned(line.replace('\t', "    "))
    } else {
        Cow::Borrowed(line)
    }
}

// --- push_str into one presized String -----------------------------------

pub fn join_baseline(parts: &[&str]) -> String {
    let mut out = String::new();
    for part in parts {
        out = out + part + ",";
    }
    out
}

pub fn join_candidate(parts: &[&str]) -> String {
    let len = parts.iter().map(|part| part.len() + 1).sum();
    let mut out = String::with_capacity(len);
    for part in parts {
        out.push_str(part);
        out.push(',');
    }
    out
}

// --- write! into a String instead of format! per item --------------------

pub fn render_baseline(pairs: &[(&str, u32)]) -> String {
    let mut out = String::new();
    for (key, value) in pairs {
        out.push_str(&format!("{key}={value};"));
    }
    out
}

pub fn render_candidate(pairs: &[(&str, u32)]) -> String {
    let mut out = String::new();
    for (key, value) in pairs {
        // fmt::Write for String never returns Err.
        write!(out, "{key}={value};").expect("String write is infallible");
    }
    out
}

// --- fixed-size stack array instead of a Vec scratch buffer --------------

/// Decimal digits of `n`, most significant first, folded into a checksum.
pub fn digits_baseline(n: u64) -> u64 {
    let mut digits = Vec::new();
    let mut rest = n;
    loop {
        digits.push((rest % 10) as u8);
        rest /= 10;
        if rest == 0 {
            break;
        }
    }
    digits
        .iter()
        .rev()
        .fold(0, |acc, &d| acc * 31 + u64::from(d))
}

pub fn digits_candidate(n: u64) -> u64 {
    // u64::MAX has 20 decimal digits, so 20 bytes always suffice.
    let mut digits = [0u8; 20];
    let mut len = 0;
    let mut rest = n;
    loop {
        digits[len] = (rest % 10) as u8;
        len += 1;
        rest /= 10;
        if rest == 0 {
            break;
        }
    }
    digits[..len]
        .iter()
        .rev()
        .fold(0, |acc, &d| acc * 31 + u64::from(d))
}

// --- borrow the contents instead of cloning the Arc ----------------------

#[inline(never)]
fn sum_owned_arc(values: Arc<Vec<u64>>) -> u64 {
    values.iter().sum()
}

#[inline(never)]
fn sum_borrowed(values: &[u64]) -> u64 {
    values.iter().sum()
}

#[unsafe(no_mangle)]
pub fn arc_clone_baseline(shared: &Arc<Vec<u64>>, rounds: u32) -> u64 {
    let mut total = 0;
    for _ in 0..rounds {
        total += sum_owned_arc(Arc::clone(shared));
    }
    total
}

#[unsafe(no_mangle)]
pub fn arc_borrow_candidate(shared: &Arc<Vec<u64>>, rounds: u32) -> u64 {
    let mut total = 0;
    for _ in 0..rounds {
        total += sum_borrowed(shared);
    }
    total
}

// --- Rc instead of Arc when the value never crosses threads --------------

#[unsafe(no_mangle)]
pub fn handles_arc_baseline(n: usize) -> usize {
    let root = Arc::new(7u64);
    let handles: Vec<Arc<u64>> = (0..n).map(|_| Arc::clone(&root)).collect();
    let count = Arc::strong_count(&root);
    drop(handles);
    count
}

#[unsafe(no_mangle)]
pub fn handles_rc_candidate(n: usize) -> usize {
    let root = Rc::new(7u64);
    let handles: Vec<Rc<u64>> = (0..n).map(|_| Rc::clone(&root)).collect();
    let count = Rc::strong_count(&root);
    drop(handles);
    count
}
