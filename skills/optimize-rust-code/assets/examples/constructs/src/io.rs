//! I/O constructs. `CountingWriter`/`CountingReader` stand in for a file
//! or socket: every call on them would be one system call on a real
//! unbuffered handle, so their call counters are the benefit oracle.
use std::io::{self, BufRead, BufReader, BufWriter, Read, Write};

#[derive(Default)]
pub struct CountingWriter {
    pub bytes: Vec<u8>,
    pub calls: usize,
}

impl Write for CountingWriter {
    fn write(&mut self, buf: &[u8]) -> io::Result<usize> {
        self.calls += 1;
        self.bytes.extend_from_slice(buf);
        Ok(buf.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

pub struct CountingReader<'a> {
    data: &'a [u8],
    pub calls: usize,
}

impl<'a> CountingReader<'a> {
    pub fn new(data: &'a [u8]) -> Self {
        Self { data, calls: 0 }
    }
}

impl Read for CountingReader<'_> {
    fn read(&mut self, buf: &mut [u8]) -> io::Result<usize> {
        self.calls += 1;
        self.data.read(buf)
    }
}

// --- BufWriter around many small writes -----------------------------------

pub fn write_rows_baseline<W: Write>(out: &mut W, rows: u32) -> io::Result<()> {
    for row in 0..rows {
        writeln!(out, "row {row}")?;
    }
    Ok(())
}

pub fn write_rows_candidate<W: Write>(
    out: &mut W,
    rows: u32,
) -> io::Result<()> {
    let mut buffered = BufWriter::new(out);
    for row in 0..rows {
        writeln!(buffered, "row {row}")?;
    }
    // Drop would flush too, but would silently ignore a write error.
    buffered.flush()
}

// --- BufReader around many small reads ------------------------------------

/// Counts newline bytes, reading one byte per call.
pub fn count_lines_baseline<R: Read>(mut input: R) -> io::Result<usize> {
    let mut byte = [0u8; 1];
    let mut lines = 0;
    while input.read(&mut byte)? == 1 {
        lines += usize::from(byte[0] == b'\n');
    }
    Ok(lines)
}

pub fn count_lines_candidate<R: Read>(input: R) -> io::Result<usize> {
    let mut reader = BufReader::new(input);
    let mut lines = 0;
    loop {
        let chunk = reader.fill_buf()?;
        if chunk.is_empty() {
            return Ok(lines);
        }
        lines += chunk.iter().filter(|&&b| b == b'\n').count();
        let consumed = chunk.len();
        reader.consume(consumed);
    }
}

// --- read_line into one reused String instead of lines() ------------------

pub fn longest_line_baseline<R: BufRead>(input: R) -> io::Result<usize> {
    let mut longest = 0;
    for line in input.lines() {
        longest = longest.max(line?.len());
    }
    Ok(longest)
}

pub fn longest_line_candidate<R: BufRead>(mut input: R) -> io::Result<usize> {
    let mut longest = 0;
    let mut line = String::new();
    loop {
        line.clear();
        if input.read_line(&mut line)? == 0 {
            return Ok(longest);
        }
        // lines() strips "\n" and a preceding "\r"; match it exactly.
        let text = line.strip_suffix('\n').unwrap_or(&line);
        let text = if line.ends_with('\n') {
            text.strip_suffix('\r').unwrap_or(text)
        } else {
            text
        };
        longest = longest.max(text.len());
    }
}

// --- lock stdout once instead of per println! ------------------------------

pub fn print_rows_baseline(rows: u32) {
    for row in 0..rows {
        println!("row {row}");
    }
}

pub fn print_rows_candidate(rows: u32) -> io::Result<()> {
    // One lock for the whole loop; StdoutLock is still line-buffered, so
    // wrap it in BufWriter as well when per-line flushing is not required.
    let mut out = io::stdout().lock();
    for row in 0..rows {
        writeln!(out, "row {row}")?;
    }
    out.flush()
}

/// Lock once and buffer: one write(2) per ~8 KiB instead of per line.
/// Output reaches the terminal only when the buffer fills or at flush.
pub fn print_rows_buffered(rows: u32) -> io::Result<()> {
    let mut out = BufWriter::new(io::stdout().lock());
    for row in 0..rows {
        writeln!(out, "row {row}")?;
    }
    out.flush()
}
