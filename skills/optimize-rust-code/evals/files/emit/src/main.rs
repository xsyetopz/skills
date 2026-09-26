//! Emits one CSV row per id: `emit <count> [stop_at]`.
//! If an id equals `stop_at`, the rows before it are kept, an error goes to
//! stderr, and the process exits with status 3 (the ingest job relies on this).

fn checksum(i: u64) -> u64 {
    i.wrapping_mul(0x9E37_79B9_7F4A_7C15) >> 40
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let count: u64 = args.get(1).and_then(|s| s.parse().ok()).unwrap_or(2_000_000);
    let stop_at: Option<u64> = args.get(2).and_then(|s| s.parse().ok());
    println!("id,checksum");
    for i in 0..count {
        if Some(i) == stop_at {
            eprintln!("refusing to emit id {i}");
            std::process::exit(3);
        }
        println!("{},{}", i, checksum(i));
    }
}
