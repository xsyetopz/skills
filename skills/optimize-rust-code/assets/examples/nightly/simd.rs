// Nightly-only: std::simd is unstable (feature `portable_simd`,
// tracking issue rust-lang/rust#86656). Not built by verify.sh; run with
//   rustc +nightly -O --edition 2024 simd.rs && ./simd
#![feature(portable_simd)]
use std::simd::f32x8;
use std::simd::num::SimdFloat;

fn sum_simd(values: &[f32]) -> f32 {
    let (chunks, tail) = values.as_chunks::<8>();
    let lanes = chunks
        .iter()
        .fold(f32x8::splat(-0.0), |acc, c| acc + f32x8::from_array(*c));
    lanes.reduce_sum() + tail.iter().sum::<f32>()
}

fn main() {
    let values: Vec<f32> = (0..4099).map(|i| (i % 17) as f32).collect();
    let serial: f32 = values.iter().sum();
    // Integer-valued inputs keep every partial sum exact, so bits match.
    assert_eq!(serial.to_bits(), sum_simd(&values).to_bits());
    println!("PASSED: simd sum = {serial}");
}
