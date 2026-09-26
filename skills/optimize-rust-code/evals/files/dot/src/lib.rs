//! Scoring kernel for the ranking service.

/// Dot product of `a` and `b[..a.len()]`.
///
/// Panics if `b` is shorter than `a`. Scores are compared against stored
/// golden values, so results must be bit-for-bit reproducible.
pub fn dot(a: &[f32], b: &[f32]) -> f32 {
    let mut s = 0.0f32;
    for i in 0..a.len() {
        s += a[i] * b[i];
    }
    s
}
