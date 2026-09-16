#![forbid(unsafe_code)]
use pairs::*;
use std::{env, error::Error, hint::black_box};

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = env::args().skip(1).collect();
    if args.len() != 3 || !matches!(args[0].as_str(), "baseline" | "candidate") {
        return Err("usage: pairs-cli baseline|candidate CASE SIZE".into());
    }
    let which: usize = args[1].parse()?;
    let size: usize = args[2].parse()?;
    if size > 100_000 { return Err("size exceeds 100000".into()); }
    let values: Vec<i64> = (0..size).map(|i| (i % 31) as i64 - 15).collect();
    let strings: Vec<String> = values.iter().map(ToString::to_string).collect();
    let candidate = args[0] == "candidate";
    match which {
        1 => println!("{:?}", black_box(if candidate { candidate_append(&values) } else { baseline_append(&values) })),
        2 => println!("{:?}", black_box(if candidate { candidate_counts(&strings) } else { baseline_counts(&strings) })),
        3 => println!("{:?}", black_box(if candidate { candidate_membership(&strings, &strings) } else { baseline_membership(&strings, &strings) })),
        4 => println!("{}", black_box(if candidate { candidate_sum(&values) } else { baseline_sum(&values) })),
        5 => println!("{:?}", black_box(if candidate { candidate_queue(&values) } else { baseline_queue(&values) })),
        6 => {
            let text = strings.join(":");
            println!("{}", black_box(if candidate { candidate_delimiters(&text) } else { baseline_delimiters(&text) }));
        },
        7 => println!("{}", black_box(if candidate { candidate_cow_clone_from_lengths(&strings) } else { baseline_owned_lengths(&strings) })),
        8 => println!("{}", black_box(if candidate { candidate_soa_x_sum(&values) } else { baseline_aos_x_sum(&values) })),
        _ => return Err("case must be 1..8".into()),
    }
    Ok(())
}
