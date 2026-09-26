//! Simplified request loop of the quote server. Each request runs inside
//! catch_unwind so one bad request cannot take the process down.

use std::panic;

fn handle(request: &str) -> String {
    let qty: u32 = request.trim().parse().expect("quantity must be a number");
    let price: u64 = (1..=u64::from(qty)).map(|i| i * 3 % 7 + 10).sum();
    format!("quote {qty} -> {price}")
}

fn main() {
    let requests: Vec<String> = std::env::args().skip(1).collect();
    for request in &requests {
        match panic::catch_unwind(|| handle(request)) {
            Ok(response) => println!("{response}"),
            Err(_) => println!("error: request {request:?} failed, server still up"),
        }
    }
}
