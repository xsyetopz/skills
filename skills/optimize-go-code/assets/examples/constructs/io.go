package constructs

import (
	"bufio"
	"io"
	"strconv"
)

// CountingWriter counts Write calls; each call models one syscall.
type CountingWriter struct {
	W     io.Writer
	Calls int
}

func (c *CountingWriter) Write(p []byte) (int, error) {
	c.Calls++
	return c.W.Write(p)
}

// CountingReader counts Read calls.
type CountingReader struct {
	R     io.Reader
	Calls int
}

func (c *CountingReader) Read(p []byte) (int, error) {
	c.Calls++
	return c.R.Read(p)
}

func WriteLinesBaseline(w io.Writer, values []int) error {
	var tmp [24]byte
	for _, v := range values {
		line := append(strconv.AppendInt(tmp[:0], int64(v), 10), '\n')
		if _, err := w.Write(line); err != nil {
			return err
		}
	}
	return nil
}

func WriteLinesCandidate(w io.Writer, values []int) error {
	bw := bufio.NewWriter(w) // 4096-byte buffer by default
	var tmp [24]byte
	for _, v := range values {
		line := append(strconv.AppendInt(tmp[:0], int64(v), 10), '\n')
		if _, err := bw.Write(line); err != nil {
			return err
		}
	}
	return bw.Flush() // without Flush the tail is silently lost
}

// SumLinesBaseline reads one byte per Read call.
func SumLinesBaseline(r io.Reader) (int, error) {
	sum, cur := 0, 0
	var b [1]byte
	for {
		n, err := r.Read(b[:])
		if n == 1 {
			if b[0] == '\n' {
				sum += cur
				cur = 0
			} else {
				cur = cur*10 + int(b[0]-'0')
			}
		}
		if err == io.EOF {
			return sum + cur, nil
		}
		if err != nil {
			return 0, err
		}
	}
}

// SumLinesCandidate scans lines through bufio.Scanner.
func SumLinesCandidate(r io.Reader) (int, error) {
	sc := bufio.NewScanner(r)
	sum := 0
	for sc.Scan() {
		n, err := strconv.Atoi(sc.Text())
		if err != nil {
			return 0, err
		}
		sum += n
	}
	return sum, sc.Err() // ErrTooLong for lines over the max token size
}
