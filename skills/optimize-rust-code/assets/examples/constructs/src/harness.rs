//! Std-only timing harness for when a benchmark dependency is not allowed.
//! It reports the median and min of `samples` batches; it has none of
//! Criterion's outlier analysis or change detection.
use std::hint::black_box;
use std::time::{Duration, Instant};

pub struct Timing {
    pub median: Duration,
    pub min: Duration,
}

/// Times `f` in `samples` batches of `batch` calls after one warm-up batch.
/// Inputs must be passed through `black_box` by the caller's closure and
/// the result is black-boxed here so the call cannot be deleted.
pub fn time<R>(samples: usize, batch: u32, mut f: impl FnMut() -> R) -> Timing {
    assert!(samples > 0 && batch > 0, "samples and batch must be > 0");
    for _ in 0..batch {
        black_box(f());
    }
    let mut per_call: Vec<Duration> = (0..samples)
        .map(|_| {
            let start = Instant::now();
            for _ in 0..batch {
                black_box(f());
            }
            start.elapsed() / batch
        })
        .collect();
    per_call.sort_unstable();
    Timing {
        median: per_call[samples / 2],
        min: per_call[0],
    }
}

pub fn report(name: &str, timing: &Timing) {
    println!(
        "TIME {name}: median {:?} min {:?} per call",
        timing.median, timing.min
    );
}
