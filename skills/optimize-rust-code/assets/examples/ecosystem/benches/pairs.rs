//! Criterion benchmarks for baseline/candidate pairs. Run through
//! `sh verify.sh measure` so build output stays in a temporary copy.
use constructs::{allocation as a, codegen as g, dispatch as d};
use criterion::{criterion_group, criterion_main, BatchSize, Criterion};
use ecosystem::*;
use std::hint::black_box;

fn allocation(c: &mut Criterion) {
    let mut group = c.benchmark_group("with-capacity");
    group.bench_function("baseline", |b| {
        b.iter(|| a::squares_baseline(black_box(4096)))
    });
    group.bench_function("candidate", |b| {
        b.iter(|| a::squares_candidate(black_box(4096)))
    });
    group.finish();
}

fn codegen(c: &mut Criterion) {
    let x: Vec<u32> = (0..4096).collect();
    let y: Vec<u32> = x.iter().map(|v| v ^ 0x5a5a).collect();
    let mut group = c.benchmark_group("bounds-check");
    group.bench_function("index", |b| {
        b.iter(|| g::dot_index_baseline(black_box(&x), black_box(&y)))
    });
    group.bench_function("zip", |b| {
        b.iter(|| g::dot_iter_candidate(black_box(&x), black_box(&y)))
    });
    group.finish();

    let floats: Vec<f32> = (0..4096).map(|i| (i % 17) as f32).collect();
    let mut group = c.benchmark_group("f32-sum");
    group.bench_function("serial", |b| {
        b.iter(|| g::sum_f32_baseline(black_box(&floats)))
    });
    group.bench_function("lanes", |b| {
        b.iter(|| g::sum_f32_candidate(black_box(&floats)))
    });
    group.finish();

    let unsorted: Vec<u32> = (0..10_000u32)
        .map(|i| i.wrapping_mul(2_654_435_761))
        .collect();
    let mut group = c.benchmark_group("sort");
    // iter_batched keeps the clone out of the measured routine.
    group.bench_function("stable", |b| {
        b.iter_batched_ref(
            || unsorted.clone(),
            |v| g::sort_baseline(v),
            BatchSize::SmallInput,
        )
    });
    group.bench_function("unstable", |b| {
        b.iter_batched_ref(
            || unsorted.clone(),
            |v| g::sort_candidate(v),
            BatchSize::SmallInput,
        )
    });
    group.finish();

    let sides: Vec<u64> = (0..1024).collect();
    let boxed = d::boxed_mixed(&sides);
    let mixed = d::enum_mixed(&sides);
    let mut group = c.benchmark_group("dispatch");
    group.bench_function("dyn", |b| {
        b.iter(|| d::total_dyn_baseline(black_box(&boxed)))
    });
    group.bench_function("enum", |b| {
        b.iter(|| d::total_enum_candidate(black_box(&mixed)))
    });
    group.finish();
}

fn ecosystem(c: &mut Criterion) {
    let keys: Vec<u32> = (0..100_000u32).map(|i| (i * 7919) % 1013).collect();
    let mut group = c.benchmark_group("hasher");
    group.bench_function("siphash", |b| {
        b.iter(|| histogram_std(black_box(&keys)))
    });
    group.bench_function("fxhash", |b| {
        b.iter(|| histogram_fx(black_box(&keys)))
    });
    group.finish();

    let inputs: Vec<u64> = (1..100_000).collect();
    let mut group = c.benchmark_group("rayon");
    group.bench_function("serial", |b| {
        b.iter(|| steps_serial(black_box(&inputs)))
    });
    group.bench_function("parallel", |b| {
        b.iter(|| steps_parallel(black_box(&inputs)))
    });
    group.finish();
}

criterion_group!(benches, allocation, codegen, ecosystem);
criterion_main!(benches);
