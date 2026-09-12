use std::collections::HashMap;

fn red(values: &[usize]) -> Vec<(usize, usize)> {
    let mut counts = Vec::new();
    for &value in values {
        if let Some((_, count)) = counts.iter_mut().find(|(key, _)| *key == value) {
            *count += 1;
        } else {
            counts.push((value, 1));
        }
    }
    counts
}

fn green(values: &[usize]) -> Vec<(usize, usize)> {
    let mut counts = HashMap::new();
    for &value in values {
        *counts.entry(value).or_insert(0) += 1;
    }
    let mut result: Vec<_> = counts.into_iter().collect();
    result.sort_unstable_by_key(|(key, _)| *key);
    result
}

fn main() {
    let mode = std::env::args().nth(1).expect("usage: benchmark red|green");
    let size = std::env::var("WORKLOAD_SIZE")
        .ok()
        .and_then(|value| value.parse().ok())
        .unwrap_or(60_000);
    let values: Vec<_> = (0..size).map(|index| index % 2_000).collect();
    let result = match mode.as_str() {
        "red" => red(&values),
        "green" => green(&values),
        _ => panic!("usage: benchmark red|green"),
    };
    let checksum: usize = result.iter().map(|(key, count)| key * count).sum();
    println!("distinct={} checksum={checksum}", result.len());
}
