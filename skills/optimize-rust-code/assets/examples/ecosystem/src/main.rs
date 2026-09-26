//! Equivalence oracle for the dependency-backed constructs.
use ecosystem::*;
use std::collections::HashMap;

fn main() {
    let keys: Vec<u32> = (0..100_000u32).map(|i| (i * 7919) % 1013).collect();
    for input in [&keys[..0], &keys[..1], &keys[..]] {
        let fx: HashMap<u32, u32> = histogram_fx(input).into_iter().collect();
        assert_eq!(histogram_std(input), fx, "fxhash: counts differ");
    }
    let inputs: Vec<u64> = (1..200_000).collect();
    for input in [&inputs[..0], &inputs[..1], &inputs[..]] {
        // Order is part of the contract: element i must stay at index i.
        assert_eq!(steps_serial(input), steps_parallel(input), "rayon order");
        assert_eq!(max_serial(input), max_parallel(input), "rayon max");
    }
    println!(
        "PASSED: fxhash and rayon oracles; rayon threads = {}",
        rayon::current_num_threads()
    );
}
