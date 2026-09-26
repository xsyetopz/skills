//! constructs verify          equivalence + allocation/call-count oracles
//! constructs smoke           run every pair once; no timing
//! constructs time [filter]   std-only Instant timing of every pair
//! constructs print-baseline|print-candidate|print-buffered ROWS
//!                            stdout-lock and buffered-stdout cards
use constructs::alloc_count::CountingAlloc;
use constructs::codegen::Gather;
use constructs::collections::{self, CountingState, Counts};
use constructs::dispatch::Shape;
use constructs::{allocation as a, check, codegen as g, dispatch as d};
use constructs::{harness, io as cio};
use std::collections::hash_map::RandomState;
use std::hint::black_box;
use std::io::Cursor;
use std::sync::Arc;

#[global_allocator]
static ALLOC: CountingAlloc = CountingAlloc;

type Run = Box<dyn FnMut()>;

struct Fixtures {
    batches: Vec<Vec<u32>>,
    text: String,
    names: Vec<String>,
    frames: Vec<Vec<u8>>,
    parts: Vec<&'static str>,
    pairs: Vec<(&'static str, u32)>,
    shared: Arc<Vec<u64>>,
    a: Vec<u32>,
    b: Vec<u32>,
    bytes: Vec<u8>,
    unsorted: Vec<u32>,
    floats: Vec<f32>,
    sides: Vec<u64>,
    keys: Vec<u32>,
}

fn fixtures() -> Fixtures {
    let a: Vec<u32> = (0..4096).map(|i| i * 7 + 1).collect();
    let text = (0..512)
        .map(|i| format!("admin{i} key{i}:value {i} alpha beta\n"))
        .collect::<String>();
    Fixtures {
        batches: (0..64).map(|i| (0..i).collect()).collect(),
        names: (0..256).map(|i| format!("admin{i}")).collect(),
        frames: (0..64).map(|i| vec![i as u8; 1024]).collect(),
        parts: ["alpha", "beta", "gamma", "delta"].repeat(64),
        pairs: (0..64).map(|i| ("key", i)).collect(),
        shared: Arc::new((0..1024).collect()),
        b: a.iter().map(|v| v ^ 0x5a5a).collect(),
        bytes: text.as_bytes().to_vec(),
        unsorted: (0..10_000u32)
            .map(|i| i.wrapping_mul(2_654_435_761))
            .collect(),
        sides: (0..1024).collect(),
        // Small integers: every partial sum is exact in f32 (< 2^24).
        floats: (0..4099).map(|i| (i % 17) as f32).collect(),
        keys: (0..4096).map(|i| i * 31).collect(),
        text,
        a,
    }
}

fn pairs(f: &'static Fixtures) -> Vec<(&'static str, Run, Run)> {
    let plan: &Gather = Box::leak(Box::new(
        g::Gather::new((0..f.a.len()).rev().collect(), f.a.len())
            .expect("valid indices"),
    ));
    let boxed: &[Box<dyn Shape>] =
        Box::leak(Box::new(d::boxed_squares(&f.sides)));
    let squares: &'static [d::Square] =
        Box::leak(f.sides.iter().map(|&s| d::Square(s)).collect());
    let mixed: &'static [d::AnyShape] =
        Box::leak(d::enum_mixed(&f.sides).into_boxed_slice());
    let boxed_mixed: &[Box<dyn Shape>] =
        Box::leak(Box::new(d::boxed_mixed(&f.sides)));
    macro_rules! pair {
        ($name:expr, $base:expr, $cand:expr) => {
            (
                $name,
                Box::new(move || {
                    black_box($base);
                }) as Run,
                Box::new(move || {
                    black_box($cand);
                }) as Run,
            )
        };
    }
    vec![
        pair!(
            "with-capacity",
            a::squares_baseline(black_box(4096)),
            a::squares_candidate(black_box(4096))
        ),
        pair!(
            "reserve-extend",
            a::flatten_baseline(black_box(&f.batches)),
            a::flatten_candidate(black_box(&f.batches))
        ),
        pair!(
            "clear-reuse",
            a::widest_baseline(black_box(&f.text)),
            a::widest_candidate(black_box(&f.text))
        ),
        pair!(
            "borrowed-params",
            a::admins_baseline(black_box(f.names.clone())),
            a::admins_candidate(black_box(&f.names))
        ),
        pair!(
            "clone-from",
            a::snapshots_baseline(black_box(&f.frames)),
            a::snapshots_candidate(black_box(&f.frames))
        ),
        pair!(
            "cow",
            a::detab_baseline(black_box("no tabs in this line at all")),
            a::detab_candidate(black_box("no tabs in this line at all"))
        ),
        pair!(
            "push-str",
            a::join_baseline(black_box(&f.parts)),
            a::join_candidate(black_box(&f.parts))
        ),
        pair!(
            "write-macro",
            a::render_baseline(black_box(&f.pairs)),
            a::render_candidate(black_box(&f.pairs))
        ),
        pair!(
            "stack-array",
            a::digits_baseline(black_box(18_446_744_073_709_551_615)),
            a::digits_candidate(black_box(18_446_744_073_709_551_615))
        ),
        pair!(
            "arc-borrow",
            a::arc_clone_baseline(black_box(&f.shared), 64),
            a::arc_borrow_candidate(black_box(&f.shared), 64)
        ),
        pair!(
            "rc-not-arc",
            a::handles_arc_baseline(black_box(1024)),
            a::handles_rc_candidate(black_box(1024))
        ),
        pair!(
            "iterator-zip",
            g::dot_index_baseline(black_box(&f.a), black_box(&f.b)),
            g::dot_iter_candidate(black_box(&f.a), black_box(&f.b))
        ),
        pair!(
            "reslice",
            {
                let mut dst = f.a.clone();
                g::add_index_baseline(black_box(&mut dst), black_box(&f.b));
                dst
            },
            {
                let mut dst = f.a.clone();
                g::add_reslice_candidate(black_box(&mut dst), black_box(&f.b));
                dst
            }
        ),
        pair!(
            "chunks-exact",
            g::words_index_baseline(black_box(&f.bytes)),
            g::words_chunks_candidate(black_box(&f.bytes))
        ),
        pair!(
            "get-unchecked",
            g::gather_checked_baseline(black_box(plan), black_box(&f.a)),
            g::gather_unchecked_candidate(black_box(plan), black_box(&f.a))
        ),
        pair!(
            "vectorize",
            g::sum_f32_baseline(black_box(&f.floats)),
            g::sum_f32_candidate(black_box(&f.floats))
        ),
        pair!(
            "inline-cross-crate",
            g::scale_all_baseline(black_box(&f.a)),
            g::scale_all_candidate(black_box(&f.a))
        ),
        pair!(
            "sort-unstable",
            {
                let mut v = f.unsorted.clone();
                g::sort_baseline(black_box(&mut v));
                v
            },
            {
                let mut v = f.unsorted.clone();
                g::sort_candidate(black_box(&mut v));
                v
            }
        ),
        pair!(
            "memchr-split-once",
            g::split_key_baseline(black_box(
                "a-rather-long-header-name-before-the-colon:value"
            )),
            g::split_key_candidate(black_box(
                "a-rather-long-header-name-before-the-colon:value"
            ))
        ),
        pair!(
            "memchr-contains",
            g::has_newline_baseline(black_box(&f.bytes[..4000])),
            g::has_newline_candidate(black_box(&f.bytes[..4000]))
        ),
        pair!(
            "generic-dispatch",
            d::total_dyn_baseline(black_box(boxed)),
            d::total_generic_candidate(black_box(squares))
        ),
        pair!(
            "enum-dispatch",
            d::total_dyn_baseline(black_box(boxed_mixed)),
            d::total_enum_candidate(black_box(mixed))
        ),
        pair!(
            "entry-api",
            {
                let mut m: Counts<RandomState> = Counts::default();
                collections::count_words_baseline(&mut m, black_box(&f.text));
                m.len()
            },
            {
                let mut m: Counts<RandomState> = Counts::default();
                collections::count_words_candidate(&mut m, black_box(&f.text));
                m.len()
            }
        ),
        pair!(
            "hashmap-capacity",
            collections::index_baseline(black_box(&f.keys)),
            collections::index_candidate(black_box(&f.keys))
        ),
        pair!(
            "bufwriter",
            {
                let mut w = cio::CountingWriter::default();
                cio::write_rows_baseline(&mut w, black_box(256)).unwrap();
                w.calls
            },
            {
                let mut w = cio::CountingWriter::default();
                cio::write_rows_candidate(&mut w, black_box(256)).unwrap();
                w.calls
            }
        ),
        pair!(
            "bufreader",
            cio::count_lines_baseline(cio::CountingReader::new(&f.bytes))
                .unwrap(),
            cio::count_lines_candidate(cio::CountingReader::new(&f.bytes))
                .unwrap()
        ),
        pair!(
            "read-line-reuse",
            cio::longest_line_baseline(Cursor::new(&f.bytes)).unwrap(),
            cio::longest_line_candidate(Cursor::new(&f.bytes)).unwrap()
        ),
    ]
}

fn verify(f: &Fixtures) {
    // Vec::with_capacity
    for n in [0, 1, 4, 1000] {
        check::equal(
            "with-capacity",
            a::squares_baseline(n),
            a::squares_candidate(n),
        );
    }
    check::fewer_allocations(
        "with-capacity",
        || a::squares_baseline(1000),
        || a::squares_candidate(1000),
    );
    // reserve + extend_from_slice
    check::equal(
        "reserve-extend",
        a::flatten_baseline(&[]),
        a::flatten_candidate(&[]),
    );
    check::equal(
        "reserve-extend",
        a::flatten_baseline(&f.batches),
        a::flatten_candidate(&f.batches),
    );
    check::fewer_allocations(
        "reserve-extend",
        || a::flatten_baseline(&f.batches),
        || a::flatten_candidate(&f.batches),
    );
    // clear() reuse
    for text in ["", "one", "a b\n\nc d e\n", &f.text] {
        check::equal(
            "clear-reuse",
            a::widest_baseline(text),
            a::widest_candidate(text),
        );
    }
    check::fewer_allocations(
        "clear-reuse",
        || a::widest_baseline(&f.text),
        || a::widest_candidate(&f.text),
    );
    // borrowed parameters: the baseline's caller must clone to keep `names`
    check::equal(
        "borrowed-params",
        a::admins_baseline(f.names.clone()),
        a::admins_candidate(&f.names),
    );
    check::fewer_allocations(
        "borrowed-params",
        || a::admins_baseline(f.names.clone()),
        || a::admins_candidate(&f.names),
    );
    // clone_from
    check::equal(
        "clone-from",
        a::snapshots_baseline(&f.frames),
        a::snapshots_candidate(&f.frames),
    );
    check::fewer_allocations(
        "clone-from",
        || a::snapshots_baseline(&f.frames),
        || a::snapshots_candidate(&f.frames),
    );
    // Cow
    for line in ["", "plain", "\tindented", "a\tb\t"] {
        check::equal(
            "cow",
            a::detab_baseline(line),
            a::detab_candidate(line).into_owned(),
        );
    }
    check::fewer_allocations(
        "cow",
        || a::detab_baseline("plain text"),
        || a::detab_candidate("plain text"),
    );
    // push_str
    check::equal("push-str", a::join_baseline(&[]), a::join_candidate(&[]));
    check::equal(
        "push-str",
        a::join_baseline(&f.parts),
        a::join_candidate(&f.parts),
    );
    check::fewer_allocations(
        "push-str",
        || a::join_baseline(&f.parts),
        || a::join_candidate(&f.parts),
    );
    // write!
    check::equal(
        "write-macro",
        a::render_baseline(&f.pairs),
        a::render_candidate(&f.pairs),
    );
    check::fewer_allocations(
        "write-macro",
        || a::render_baseline(&f.pairs),
        || a::render_candidate(&f.pairs),
    );
    // stack array
    for n in [0, 7, 10, 1_234_567_890, u64::MAX] {
        check::equal(
            "stack-array",
            a::digits_baseline(n),
            a::digits_candidate(n),
        );
    }
    check::fewer_allocations(
        "stack-array",
        || a::digits_baseline(u64::MAX),
        || a::digits_candidate(u64::MAX),
    );
    // Arc borrow / Rc (benefit is asserted in assembly: verify.sh asm)
    check::equal(
        "arc-borrow",
        a::arc_clone_baseline(&f.shared, 3),
        a::arc_borrow_candidate(&f.shared, 3),
    );
    check::equal("arc-borrow", Arc::strong_count(&f.shared), 1);
    check::equal(
        "rc-not-arc",
        a::handles_arc_baseline(5),
        a::handles_rc_candidate(5),
    );

    // Codegen pairs: equivalence here, benefit in verify.sh asm.
    for n in [0, 1, 3, 4096] {
        let (x, y) = (&f.a[..n], &f.b[..n]);
        check::equal(
            "iterator-zip",
            g::dot_index_baseline(x, y),
            g::dot_iter_candidate(x, y),
        );
        let (mut p, mut q) = (x.to_vec(), x.to_vec());
        g::add_index_baseline(&mut p, y);
        g::add_reslice_candidate(&mut q, y);
        check::equal("reslice", p, q);
        check::equal(
            "inline-cross-crate",
            g::scale_all_baseline(x),
            g::scale_all_candidate(x),
        );
    }
    // Both panic when b is shorter than a (panic kind is the contract).
    // Under panic = "abort", catch_unwind cannot catch: the process
    // aborts. That is the panic=abort card's semantic trap.
    if cfg!(panic = "unwind") {
        let short = |run: fn(&[u32], &[u32]) -> u32| {
            std::panic::catch_unwind(|| run(&[1, 2], &[1])).is_err()
        };
        let hook = std::panic::take_hook();
        std::panic::set_hook(Box::new(|_| {})); // expected panics: quiet
        let panics =
            (short(g::dot_index_baseline), short(g::dot_iter_candidate));
        std::panic::set_hook(hook);
        check::equal("iterator-zip-panics", panics, (true, true));
    } else {
        println!("SKIPPED iterator-zip-panics: panic=abort build");
    }
    for len in [0, 1, 7, 8, 9, 4099] {
        let x = &f.floats[..len];
        check::equal(
            "vectorize",
            g::sum_f32_baseline(x).to_bits(),
            g::sum_f32_candidate(x).to_bits(),
        );
    }
    check::equal(
        "target-feature",
        g::sum_u32_portable(&f.a),
        g::sum_u32_dispatch(&f.a),
    );
    for len in [0, 3, 4, 7, 4001] {
        let bytes = &f.bytes[..len];
        check::equal(
            "chunks-exact",
            g::words_index_baseline(bytes),
            g::words_chunks_candidate(bytes),
        );
    }
    let plan = g::Gather::new(vec![3, 0, 3, 1], 4).expect("valid");
    check::equal(
        "get-unchecked",
        g::gather_checked_baseline(&plan, &[1, 2, 3, 4]),
        g::gather_unchecked_candidate(&plan, &[1, 2, 3, 4]),
    );
    check::equal(
        "get-unchecked-rejects",
        g::Gather::new(vec![4], 4).is_none(),
        true,
    );
    // sort_unstable: same output; the stable sort allocates a buffer
    let (mut s1, mut s2) = (f.unsorted.clone(), f.unsorted.clone());
    g::sort_baseline(&mut s1);
    g::sort_candidate(&mut s2);
    check::equal("sort-unstable", s1, s2);
    let (mut s1, mut s2) = (f.unsorted.clone(), f.unsorted.clone());
    check::fewer_allocations(
        "sort-unstable",
        || {
            s1.copy_from_slice(&f.unsorted);
            g::sort_baseline(&mut s1);
        },
        || {
            s2.copy_from_slice(&f.unsorted);
            g::sort_candidate(&mut s2);
        },
    );
    for line in ["", ":", "k:v", "no colon", "é:ü:x", "a::b"] {
        check::equal(
            "split-once",
            g::split_key_baseline(line),
            g::split_key_candidate(line),
        );
    }
    for bytes in [&b""[..], b"x", b"\n", &f.bytes] {
        check::equal(
            "memchr-contains",
            g::has_newline_baseline(bytes),
            g::has_newline_candidate(bytes),
        );
    }
    // Dispatch
    let squares: Vec<d::Square> =
        f.sides.iter().map(|&s| d::Square(s)).collect();
    check::equal(
        "generic-dispatch",
        d::total_dyn_baseline(&d::boxed_squares(&f.sides)),
        d::total_generic_candidate(&squares),
    );
    check::fewer_allocations(
        "generic-dispatch",
        || d::boxed_squares(&f.sides),
        || f.sides.iter().map(|&s| d::Square(s)).collect::<Vec<_>>(),
    );
    check::equal(
        "enum-dispatch",
        d::total_dyn_baseline(&d::boxed_mixed(&f.sides)),
        d::total_enum_candidate(&d::enum_mixed(&f.sides)),
    );
    check::fewer_allocations(
        "enum-dispatch",
        || d::boxed_mixed(&f.sides),
        || d::enum_mixed(&f.sides),
    );
    // Entry API: identical counts, fewer hash computations
    let text = "b a b c b a";
    let mut base: Counts<CountingState> = Counts::default();
    let mut cand: Counts<CountingState> = Counts::default();
    collections::count_words_baseline(&mut base, text);
    collections::count_words_candidate(&mut cand, text);
    check::equal("entry-api", sorted(&base), sorted(&cand));
    let base_hashes = base.hasher().hashes.get();
    let cand_hashes = cand.hasher().hashes.get();
    check::fewer("entry-api", "hash computations", base_hashes, cand_hashes);
    // HashMap::with_capacity
    check::equal(
        "hashmap-capacity",
        collections::index_baseline(&f.keys),
        collections::index_candidate(&f.keys),
    );
    check::fewer_allocations(
        "hashmap-capacity",
        || collections::index_baseline(&f.keys),
        || collections::index_candidate(&f.keys),
    );
    // BufWriter: same bytes, fewer calls on the inner writer
    let (mut w1, mut w2) = (
        cio::CountingWriter::default(),
        cio::CountingWriter::default(),
    );
    cio::write_rows_baseline(&mut w1, 1000).expect("in-memory write");
    cio::write_rows_candidate(&mut w2, 1000).expect("in-memory write");
    check::equal("bufwriter", &w1.bytes, &w2.bytes);
    check::fewer("bufwriter", "inner write calls", w1.calls, w2.calls);
    // BufReader: same answer, fewer calls on the inner reader
    let mut r1 = cio::CountingReader::new(&f.bytes);
    let mut r2 = cio::CountingReader::new(&f.bytes);
    let l1 = cio::count_lines_baseline(&mut r1).expect("in-memory read");
    let l2 = cio::count_lines_candidate(&mut r2).expect("in-memory read");
    check::equal("bufreader", l1, l2);
    check::fewer("bufreader", "inner read calls", r1.calls, r2.calls);
    // read_line reuse: same answer including "\r\n" and a missing final "\n"
    for input in [&b""[..], b"a\r\nbbb\n", b"cc\rdd", b"x\n\n", &f.bytes] {
        check::equal(
            "read-line-reuse",
            cio::longest_line_baseline(Cursor::new(input)).expect("utf-8"),
            cio::longest_line_candidate(Cursor::new(input)).expect("utf-8"),
        );
    }
    check::fewer_allocations(
        "read-line-reuse",
        || cio::longest_line_baseline(Cursor::new(&f.bytes)),
        || cio::longest_line_candidate(Cursor::new(&f.bytes)),
    );
}

fn sorted<S>(counts: &Counts<'_, S>) -> Vec<(String, usize)> {
    let mut out: Vec<_> =
        counts.iter().map(|(k, v)| (k.to_string(), *v)).collect();
    out.sort();
    out
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let mode = args.first().map_or("verify", String::as_str);
    let fixtures: &'static Fixtures = Box::leak(Box::new(fixtures()));
    match mode {
        "verify" => {
            verify(fixtures);
            println!("PASSED: {} checks", check::count());
        }
        "smoke" => {
            let mut all = pairs(fixtures);
            for (_, baseline, candidate) in &mut all {
                baseline();
                candidate();
            }
            println!(
                "SMOKE PASSED: {} pairs ran once; not a timing result.",
                all.len()
            );
        }
        "time" => {
            let filter = args.get(1).map_or("", String::as_str);
            for (name, mut baseline, mut candidate) in pairs(fixtures) {
                if name.contains(filter) {
                    harness::report(
                        &format!("{name} baseline"),
                        &harness::time(31, 64, &mut baseline),
                    );
                    harness::report(
                        &format!("{name} candidate"),
                        &harness::time(31, 64, &mut candidate),
                    );
                }
            }
        }
        "print-baseline" | "print-candidate" | "print-buffered" => {
            let rows =
                args.get(1).and_then(|r| r.parse().ok()).unwrap_or(100_000);
            match mode {
                "print-baseline" => cio::print_rows_baseline(rows),
                "print-candidate" => {
                    cio::print_rows_candidate(rows).expect("stdout write")
                }
                _ => cio::print_rows_buffered(rows).expect("stdout write"),
            }
        }
        _ => {
            eprintln!(
                "usage: constructs [verify|smoke|time [filter]\
                 |print-baseline|print-candidate|print-buffered ROWS]"
            );
            std::process::exit(2);
        }
    }
}
