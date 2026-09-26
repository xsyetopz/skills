//! Upstream crate for the cross-crate `#[inline]` card. Both functions
//! contain a call (`expect`'s panic path), so rustc's automatic
//! cross-crate inlining of call-free leaf functions (Rust 1.75+) does not
//! apply and the attribute alone decides whether the body is exported.

/// Baseline: no `#[inline]`; downstream crates see only a symbol.
pub fn scale(x: u32) -> u32 {
    x.checked_mul(3).expect("scale overflow")
}

/// Candidate: `#[inline]` exports the body for downstream inlining.
#[inline]
pub fn scale_inline(x: u32) -> u32 {
    x.checked_mul(3).expect("scale overflow")
}
