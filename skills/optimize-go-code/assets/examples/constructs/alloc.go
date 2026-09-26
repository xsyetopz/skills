// Package constructs holds baseline/candidate pairs for the Go performance
// construct cards. Every pair computes the same observable result; the
// tests in *_test.go prove equivalence and the claimed metric change.
package constructs

import (
	"bytes"
	"fmt"
	"maps"
	"slices"
	"sort"
	"strconv"
	"strings"
	"sync"
)

// --- Preallocated slice capacity -----------------------------------------

func SquaresBaseline(values []int) []int {
	var out []int
	for _, v := range values {
		out = append(out, v*v)
	}
	return out
}

func SquaresCandidate(values []int) []int {
	// Non-nil even for empty input; see the card for the nil/empty contract.
	out := make([]int, 0, len(values))
	for _, v := range values {
		out = append(out, v*v)
	}
	return out
}

// --- Map size hint ---------------------------------------------------------

func IndexBaseline(keys []string) map[string]int {
	index := make(map[string]int)
	for i, k := range keys {
		index[k] = i
	}
	return index
}

func IndexCandidate(keys []string) map[string]int {
	index := make(map[string]int, len(keys))
	for i, k := range keys {
		index[k] = i
	}
	return index
}

// --- strings.Builder with Grow --------------------------------------------

func JoinBaseline(parts []string, sep string) string {
	out := ""
	for i, p := range parts {
		if i > 0 {
			out += sep
		}
		out += p
	}
	return out
}

func JoinCandidate(parts []string, sep string) string {
	if len(parts) == 0 {
		return ""
	}
	n := len(sep) * (len(parts) - 1)
	for _, p := range parts {
		n += len(p)
	}
	var b strings.Builder
	b.Grow(n)
	for i, p := range parts {
		if i > 0 {
			b.WriteString(sep)
		}
		b.WriteString(p)
	}
	return b.String()
}

// --- strconv instead of fmt -----------------------------------------------

func CSVBaseline(values []int) string {
	var b strings.Builder
	for i, v := range values {
		if i > 0 {
			b.WriteByte(',')
		}
		b.WriteString(fmt.Sprintf("%d", v))
	}
	return b.String()
}

func CSVCandidate(values []int) string {
	// 20 bytes holds any int64 in base 10 plus sign; 1 for the comma.
	buf := make([]byte, 0, len(values)*21)
	for i, v := range values {
		if i > 0 {
			buf = append(buf, ',')
		}
		buf = strconv.AppendInt(buf, int64(v), 10)
	}
	return string(buf)
}

// --- bytes.Buffer reused with Reset ---------------------------------------

func RenderBaseline(rows []string) []byte {
	var buf bytes.Buffer
	for _, r := range rows {
		buf.WriteString(r)
		buf.WriteByte('\n')
	}
	return buf.Bytes()
}

// Renderer owns one buffer. The slice returned by Render aliases that buffer
// and is valid only until the next Render call on the same Renderer.
type Renderer struct{ buf bytes.Buffer }

func (r *Renderer) Render(rows []string) []byte {
	r.buf.Reset()
	for _, row := range rows {
		r.buf.WriteString(row)
		r.buf.WriteByte('\n')
	}
	return r.buf.Bytes()
}

// --- []byte to string conversion in map lookups ---------------------------

func LookupBaseline(m map[string]int, words [][]byte) int {
	total := 0
	for _, w := range words {
		key := string(w)
		total += m[key]
		keep(key)
	}
	return total
}

func LookupCandidate(m map[string]int, words [][]byte) int {
	total := 0
	for _, w := range words {
		total += m[string(w)] // no allocation: see the conversion card
	}
	return total
}

// keep models a realistic use of the converted key (logging, storing) that
// forces the string to exist beyond the lookup.
var kept string

func keep(s string) { kept = s }

// --- sync.Pool of *bytes.Buffer --------------------------------------------

func EncodeBaseline(fields []string) string {
	buf := new(bytes.Buffer)
	buf.Grow(256)
	for _, f := range fields {
		buf.WriteString(strconv.Quote(f))
		buf.WriteByte(' ')
	}
	return buf.String()
}

var bufPool = sync.Pool{New: func() any { return new(bytes.Buffer) }}

func EncodeCandidate(fields []string) string {
	buf := bufPool.Get().(*bytes.Buffer)
	buf.Reset() // PERF/SAFETY: pooled buffers carry previous contents.
	for _, f := range fields {
		buf.Write(strconv.AppendQuote(buf.AvailableBuffer(), f))
		buf.WriteByte(' ')
	}
	s := buf.String() // copies; buf may be reused after Put
	if buf.Cap() <= 64<<10 {
		bufPool.Put(buf) // do not pool oversized buffers
	}
	return s
}

// --- sync.Pool element shape: *[]byte, not []byte -------------------------

var slicePool = sync.Pool{New: func() any { return make([]byte, 0, 512) }}

func ChecksumSlicePool(data []byte) uint32 {
	buf := slicePool.Get().([]byte)[:0]
	buf = append(buf, data...)
	sum := fold(buf)
	slicePool.Put(buf) // converting []byte to any allocates a header
	return sum
}

var ptrPool = sync.Pool{New: func() any {
	b := make([]byte, 0, 512)
	return &b
}}

func ChecksumPtrPool(data []byte) uint32 {
	p := ptrPool.Get().(*[]byte)
	buf := append((*p)[:0], data...)
	sum := fold(buf)
	*p = buf
	ptrPool.Put(p) // pointer fits in the interface word: no allocation
	return sum
}

func fold(b []byte) uint32 {
	h := uint32(2166136261)
	for _, c := range b {
		h = (h ^ uint32(c)) * 16777619
	}
	return h
}

// --- clear() to reuse a map -----------------------------------------------

func BatchCountsBaseline(batches [][]string) int {
	distinct := 0
	for _, batch := range batches {
		seen := make(map[string]struct{})
		for _, s := range batch {
			seen[s] = struct{}{}
		}
		distinct += len(seen)
	}
	return distinct
}

func BatchCountsCandidate(batches [][]string) int {
	distinct := 0
	seen := make(map[string]struct{})
	for _, batch := range batches {
		clear(seen) // keeps the allocated buckets for the next batch
		for _, s := range batch {
			seen[s] = struct{}{}
		}
		distinct += len(seen)
	}
	return distinct
}

// --- Struct keys instead of concatenated string keys ----------------------

type routeKey struct{ method, path string }

func BuildRoutesBaseline(methods, paths []string) map[string]int {
	m := make(map[string]int, len(methods))
	for i := range methods {
		m[methods[i]+" "+paths[i]] = i
	}
	return m
}

func RouteBaseline(m map[string]int, method, path string) (int, bool) {
	v, ok := m[method+" "+path]
	return v, ok
}

func BuildRoutesCandidate(methods, paths []string) map[routeKey]int {
	m := make(map[routeKey]int, len(methods))
	for i := range methods {
		m[routeKey{methods[i], paths[i]}] = i
	}
	return m
}

func RouteCandidate(m map[routeKey]int, method, path string) (int, bool) {
	v, ok := m[routeKey{method, path}]
	return v, ok
}

// --- slices.Sort instead of sort.Slice ------------------------------------

func SortBaseline(xs []int) {
	sort.Slice(xs, func(i, j int) bool { return xs[i] < xs[j] })
}

func SortCandidate(xs []int) { slices.Sort(xs) }

// --- Deterministic map order: presized keys + slices.Sort -----------------

func SortedKeysBaseline(m map[string]int) []string {
	return slices.Sorted(maps.Keys(m))
}

func SortedKeysCandidate(m map[string]int) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	slices.Sort(keys)
	return keys
}

// --- Copy a small sub-slice out of a large buffer -------------------------

func HeaderBaseline(packet []byte) []byte { return packet[:8] }

func HeaderCandidate(packet []byte) []byte {
	return bytes.Clone(packet[:8]) // releases the large backing array
}
