//go:build !race

// Allocation oracles. The race detector changes allocation counts, so this
// file is excluded from -race builds (verify.sh race).

package constructs

import (
	"strings"
	"testing"
)

// allocs returns testing.AllocsPerRun over 100 runs after one warm-up.
func allocs(f func()) float64 { return testing.AllocsPerRun(100, f) }

// fewer asserts the candidate allocates strictly less than the baseline and
// logs both so verify.sh output records the counts.
func fewer(t *testing.T, name string, baseline, candidate func()) {
	t.Helper()
	b, c := allocs(baseline), allocs(candidate)
	t.Logf("ALLOCS %s: %.0f -> %.0f per op", name, b, c)
	if c >= b {
		t.Fatalf("%s: candidate %.0f allocs/op, baseline %.0f", name, c, b)
	}
}

func none(t *testing.T, name string, f func()) {
	t.Helper()
	if n := allocs(f); n != 0 {
		t.Fatalf("%s: %.0f allocs/op, want 0", name, n)
	}
}

var (
	sinkInts   []int
	sinkMap    map[string]int
	sinkStr    string
	sinkByte   []byte
	sinkInt    int
	sinkUint32 uint32
	sinkF64    float64
	sinkHeader Header
	sinkHdrPtr *Header
)

func TestAllocsPrealloc(t *testing.T) {
	in := ints(1000)
	fewer(t, "prealloc-slice",
		func() { sinkInts = SquaresBaseline(in) },
		func() { sinkInts = SquaresCandidate(in) })
}

func TestAllocsMapHint(t *testing.T) {
	w := words(1000)
	fewer(t, "map-size-hint",
		func() { sinkMap = IndexBaseline(w) },
		func() { sinkMap = IndexCandidate(w) })
}

func TestAllocsBuilder(t *testing.T) {
	w := words(100)
	fewer(t, "strings-builder",
		func() { sinkStr = JoinBaseline(w, ",") },
		func() { sinkStr = JoinCandidate(w, ",") })
	if n := allocs(func() { sinkStr = JoinCandidate(w, ",") }); n != 1 {
		t.Fatalf("Grow must leave exactly one allocation, got %.0f", n)
	}
}

func TestAllocsStrconv(t *testing.T) {
	in := ints(200)
	fewer(t, "strconv-append",
		func() { sinkStr = CSVBaseline(in) },
		func() { sinkStr = CSVCandidate(in) })
}

func TestAllocsBufferReuse(t *testing.T) {
	rows := words(100)
	var r Renderer
	fewer(t, "buffer-reset",
		func() { sinkByte = RenderBaseline(rows) },
		func() { sinkByte = r.Render(rows) })
	none(t, "buffer-reset", func() { sinkByte = r.Render(rows) })
}

func TestAllocsConversion(t *testing.T) {
	keys, m := longKeys(100)
	fewer(t, "map-string-bytes",
		func() { sinkInt = LookupBaseline(m, keys) },
		func() { sinkInt = LookupCandidate(m, keys) })
	none(t, "map-string-bytes", func() { sinkInt = LookupCandidate(m, keys) })
}

func TestAllocsPool(t *testing.T) {
	f := words(20)
	fewer(t, "sync-pool-buffer",
		func() { sinkStr = EncodeBaseline(f) },
		func() { sinkStr = EncodeCandidate(f) })
	d := []byte(strings.Repeat("x", 300))
	fewer(t, "sync-pool-pointer",
		func() { sinkUint32 = ChecksumSlicePool(d) },
		func() { sinkUint32 = ChecksumPtrPool(d) })
}

func TestAllocsClear(t *testing.T) {
	batches := [][]string{words(200), words(200), words(200)}
	fewer(t, "clear-map",
		func() { sinkInt = BatchCountsBaseline(batches) },
		func() { sinkInt = BatchCountsCandidate(batches) })
}

func TestAllocsStructKey(t *testing.T) {
	// The concatenated key must exceed 32 bytes, or the compiler builds it
	// in a stack buffer and the baseline shows 0 allocs.
	const long = "/api/v1/organizations/members/settings"
	methods := []string{"GET", "POST", "DELETE"}
	paths := []string{long, "/api/v1/orders", "/x"}
	mb := BuildRoutesBaseline(methods, paths)
	mc := BuildRoutesCandidate(methods, paths)
	fewer(t, "struct-key",
		func() { sinkInt, _ = RouteBaseline(mb, "GET", long) },
		func() { sinkInt, _ = RouteCandidate(mc, "GET", long) })
}

func TestAllocsSort(t *testing.T) {
	src := ints(500)
	buf := make([]int, len(src))
	fewer(t, "slices-sort",
		func() { copy(buf, src); SortBaseline(buf) },
		func() { copy(buf, src); SortCandidate(buf) })
}

func TestAllocsSortedKeys(t *testing.T) {
	_, m := longKeys(500)
	var keys []string
	fewer(t, "sorted-keys",
		func() { keys = SortedKeysBaseline(m) },
		func() { keys = SortedKeysCandidate(m) })
	_ = keys
}

func TestAllocsEscape(t *testing.T) {
	line := "Content-Type: application/json"
	fewer(t, "return-by-value",
		func() { sinkHdrPtr = ParseHeaderBaseline(line) },
		func() { sinkHeader, _ = ParseHeaderCandidate(line) })
}

func TestAllocsBoxing(t *testing.T) {
	r := rects(200)
	fewer(t, "generic-no-boxing",
		func() { sinkF64 = AreaBaseline(r) },
		func() { sinkF64 = AreaCandidate(r) })
}
