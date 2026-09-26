package constructs

import (
	"errors"
	"fmt"
)

var ErrShort = errors.New("short buffer")

// Reader decodes little-endian uint16 values from a byte slice.
type Reader struct {
	buf []byte
	off int
}

// Uint16Baseline formats its error inline; the fmt.Errorf call pushes the
// inlining cost over the budget of 80.
func (r *Reader) Uint16Baseline() (uint16, error) {
	if r.off+2 > len(r.buf) {
		return 0, fmt.Errorf("offset %d of %d: %w",
			r.off, len(r.buf), ErrShort)
	}
	v := uint16(r.buf[r.off]) | uint16(r.buf[r.off+1])<<8
	r.off += 2
	return v, nil
}

// ShortError defers formatting to Error(), which only the cold path pays.
type ShortError struct{ Off, Len int }

func (e *ShortError) Error() string {
	return fmt.Sprintf("offset %d of %d: %v", e.Off, e.Len, ErrShort)
}

func (e *ShortError) Unwrap() error { return ErrShort }

// Uint16Candidate is cheap enough to inline into its callers.
func (r *Reader) Uint16Candidate() (uint16, error) {
	if r.off+2 > len(r.buf) {
		return 0, &ShortError{Off: r.off, Len: len(r.buf)}
	}
	v := uint16(r.buf[r.off]) | uint16(r.buf[r.off+1])<<8
	r.off += 2
	return v, nil
}

// SumUint16Baseline and SumUint16Candidate are the hot callers.
func SumUint16Baseline(data []byte) (int, error) {
	r := Reader{buf: data}
	sum := 0
	for range len(data) / 2 {
		v, err := r.Uint16Baseline()
		if err != nil {
			return 0, err
		}
		sum += int(v)
	}
	return sum, nil
}

func SumUint16Candidate(data []byte) (int, error) {
	r := Reader{buf: data}
	sum := 0
	for range len(data) / 2 {
		v, err := r.Uint16Candidate()
		if err != nil {
			return 0, err
		}
		sum += int(v)
	}
	return sum, nil
}
