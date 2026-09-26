use std::io::Read;

fn main() {
    let mut text = String::new();
    std::io::stdin().read_to_string(&mut text).expect("read stdin");
    let summary = logparse::summarize(&text);
    println!("rows={} max_fields={}", summary.rows, summary.max_fields);
    for (service, n) in &summary.errors_by_service {
        println!("{service}\t{n}");
    }
}
