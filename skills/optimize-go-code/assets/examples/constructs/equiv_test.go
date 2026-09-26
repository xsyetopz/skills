package constructs

import (
	"bufio"
	"bytes"
	"errors"
	"maps"
	"reflect"
	"slices"
	"strings"
	"testing"
)

// Equivalence oracles: baseline and candidate on the same inputs, including
// empty and boundary cases. Run under -race as well (verify.sh race).

func TestPreallocEquivalent(t *testing.T) {
	for _, n := range []int{0, 1, 1000} {
		in := ints(n)
		if !slices.Equal(SquaresBaseline(in), SquaresCandidate(in)) {
			t.Fatalf("n=%d", n)
		}
	}
	// Nil/empty contract differs: baseline returns nil for empty input.
	if SquaresBaseline(nil) != nil || SquaresCandidate(nil) == nil {
		t.Fatal("nil/empty contract changed; callers comparing to nil break")
	}
}

func TestAppendAliasing(t *testing.T) {
	// append into spare capacity overwrites another view of the same array.
	owner := make([]int, 1, 2)
	view := append(owner, 2)
	_ = append(owner, 3)
	if view[1] != 3 {
		t.Fatal("aliasing hazard not reproduced")
	}
	safe := append(slices.Clip(owner), 2) // Clip forces a copy on append
	_ = append(owner, 4)
	if safe[1] != 2 {
		t.Fatal("slices.Clip did not isolate the view")
	}
}

func TestMapHintEquivalent(t *testing.T) {
	for _, n := range []int{0, 1, 1000} {
		w := words(n)
		if !maps.Equal(IndexBaseline(w), IndexCandidate(w)) {
			t.Fatalf("n=%d", n)
		}
	}
}

func TestJoinEquivalent(t *testing.T) {
	cases := [][]string{nil, {""}, {"a"}, {"a", "", "é", "🙂"}, words(200)}
	for _, c := range cases {
		for _, sep := range []string{"", ", "} {
			want := strings.Join(c, sep)
			if JoinBaseline(c, sep) != want || JoinCandidate(c, sep) != want {
				t.Fatalf("%q %q", c, sep)
			}
		}
	}
}

func TestCSVEquivalent(t *testing.T) {
	extremes := []int{0, -1, 1 << 62, -(1 << 63), 1<<63 - 1}
	for _, in := range [][]int{nil, extremes, ints(500)} {
		if CSVBaseline(in) != CSVCandidate(in) {
			t.Fatalf("%v", in)
		}
	}
}

func TestRenderEquivalentAndAliasing(t *testing.T) {
	var r Renderer
	rows := words(50)
	if !bytes.Equal(RenderBaseline(rows), r.Render(rows)) {
		t.Fatal("render differs")
	}
	first := r.Render([]string{"first"})
	saved := bytes.Clone(first)
	r.Render([]string{"XXXXX"})
	if bytes.Equal(first, saved) {
		t.Fatal("expected aliasing: Render result is reused storage")
	}
}

func TestLookupEquivalent(t *testing.T) {
	keys, m := longKeys(300)
	keys = append(keys, []byte("missing"), nil)
	if LookupBaseline(m, keys) != LookupCandidate(m, keys) {
		t.Fatal("lookup differs")
	}
}

func TestPoolEquivalent(t *testing.T) {
	for _, f := range [][]string{nil, {""}, {"a\"b", "é\x00"}, words(100)} {
		want := EncodeBaseline(f)
		for range 3 { // reuse must not leak previous contents
			if got := EncodeCandidate(f); got != want {
				t.Fatalf("%q != %q", got, want)
			}
		}
	}
	for _, d := range [][]byte{nil, []byte("abc"), bytes.Repeat([]byte{7}, 900)} {
		if ChecksumSlicePool(d) != ChecksumPtrPool(d) {
			t.Fatal("checksum differs")
		}
	}
}

func TestPoolConcurrent(t *testing.T) {
	f := words(50)
	want := EncodeBaseline(f)
	done := make(chan string)
	for range 8 {
		go func() {
			got := ""
			for range 200 {
				if got = EncodeCandidate(f); got != want {
					break
				}
			}
			done <- got
		}()
	}
	for range 8 {
		if got := <-done; got != want {
			t.Fatal("concurrent pooled encode differs")
		}
	}
}

func TestClearEquivalent(t *testing.T) {
	batches := [][]string{words(100), nil, {"x", "x"}, words(10)}
	if BatchCountsBaseline(batches) != BatchCountsCandidate(batches) {
		t.Fatal("clear changed results")
	}
}

func TestStructKeysEquivalentAndUnambiguous(t *testing.T) {
	methods := []string{"GET", "POST", "GET"}
	paths := []string{"/a", "/a", "/b c"}
	mb := BuildRoutesBaseline(methods, paths)
	mc := BuildRoutesCandidate(methods, paths)
	for i := range methods {
		vb, okb := RouteBaseline(mb, methods[i], paths[i])
		vc, okc := RouteCandidate(mc, methods[i], paths[i])
		if vb != vc || okb != okc {
			t.Fatal("route differs")
		}
	}
	// The concatenated key collides: ("GET /b", "c") == ("GET", "/b c").
	_, okb := RouteBaseline(mb, "GET /b", "c")
	_, okc := RouteCandidate(mc, "GET /b", "c")
	if !okb || okc {
		t.Fatal("expected a baseline collision the struct key avoids")
	}
}

func TestSortEquivalent(t *testing.T) {
	for _, n := range []int{0, 1, 1000} {
		a, b := ints(n), ints(n)
		SortBaseline(a)
		SortCandidate(b)
		if !slices.Equal(a, b) || !slices.IsSorted(b) {
			t.Fatalf("n=%d", n)
		}
	}
}

func TestSortedKeysEquivalent(t *testing.T) {
	_, m := longKeys(200)
	for range 5 { // map iteration order varies per run
		if !slices.Equal(SortedKeysBaseline(m), SortedKeysCandidate(m)) {
			t.Fatal("keys differ")
		}
	}
	empty := map[string]int{}
	if SortedKeysBaseline(empty) != nil || SortedKeysCandidate(empty) == nil {
		t.Fatal("nil/empty contract: Sorted returns nil for empty input")
	}
}

func TestHeaderRetention(t *testing.T) {
	packet := make([]byte, 1<<20)
	copy(packet, "HDR12345payload")
	b, c := HeaderBaseline(packet), HeaderCandidate(packet)
	if !bytes.Equal(b, c) {
		t.Fatal("header differs")
	}
	if cap(b) != 1<<20 || cap(c) >= 1<<10 {
		t.Fatalf("caps %d %d: baseline must pin 1 MiB, candidate must not",
			cap(b), cap(c))
	}
	packet[0] = 'X' // a snapshot must not see later owner writes
	if c[0] != 'H' || b[0] != 'X' {
		t.Fatal("snapshot independence")
	}
}

func TestHeaderParseEquivalent(t *testing.T) {
	for _, line := range []string{"", ":", "a:b", " Host : x ", "bad name:v",
		"k:v:w", "\tk:v"} {
		p := ParseHeaderBaseline(line)
		h, ok := ParseHeaderCandidate(line)
		if (p != nil) != ok || (p != nil && *p != h) {
			t.Fatalf("%q", line)
		}
	}
}

func TestDotEquivalent(t *testing.T) {
	a, b := ints(100), ints(120)
	if DotBaseline(a, b) != DotCandidate(a, b) {
		t.Fatal("dot differs")
	}
	for _, f := range []func([]int, []int) int{DotBaseline, DotCandidate} {
		func() {
			defer func() {
				if recover() == nil {
					t.Fatal("short b must panic in both")
				}
			}()
			f(a, b[:50])
		}()
	}
}

func TestInlineEquivalent(t *testing.T) {
	data := []byte{1, 2, 3, 4, 5}
	rb, rc := Reader{buf: data}, Reader{buf: data}
	for {
		vb, eb := rb.Uint16Baseline()
		vc, ec := rc.Uint16Candidate()
		if vb != vc || (eb == nil) != (ec == nil) {
			t.Fatal("reader differs")
		}
		if eb != nil {
			if !errors.Is(ec, ErrShort) || eb.Error() != ec.Error() {
				t.Fatalf("errors %v %v", eb, ec)
			}
			return
		}
	}
}

func TestReceivers(t *testing.T) {
	var s Stats
	s.Buckets[3] = 5
	if s.TotalValue() != s.TotalPointer() {
		t.Fatal("totals differ")
	}
	s.AddValue(3)
	if s.Count != 0 {
		t.Fatal("value receiver mutated the original")
	}
	s.AddPointer(3)
	if s.Count != 1 || s.Buckets[3] != 6 {
		t.Fatal("pointer receiver must mutate the original")
	}
}

func TestInterfaceEquivalentAndTypedNil(t *testing.T) {
	r := rects(100)
	if AreaBaseline(r) != AreaCandidate(r) {
		t.Fatal("area differs")
	}
	var p *Rect
	var s any = p // interface holding a typed nil pointer
	if s == nil {
		t.Fatal("typed nil inside an interface must compare non-nil")
	}
}

func TestPadding(t *testing.T) {
	var a EventPadded
	var b EventPacked
	if reflect.TypeOf(a).Size() <= reflect.TypeOf(b).Size() {
		t.Fatal("reordering must shrink the struct")
	}
	t.Logf("EventPadded %d B, EventPacked %d B",
		reflect.TypeOf(a).Size(), reflect.TypeOf(b).Size())
}

func TestDeferInLoop(t *testing.T) {
	var hb, hc Handles
	if ProcessBaseline(&hb, 100) != ProcessCandidate(&hc, 100) {
		t.Fatal("results differ")
	}
	if hb.Live != 0 || hc.Live != 0 {
		t.Fatal("leak")
	}
	if hb.Peak != 100 || hc.Peak != 1 {
		t.Fatalf("peak open handles %d -> %d, want 100 -> 1", hb.Peak, hc.Peak)
	}
	c := Counter{n: map[string]int{"k": 7}}
	if c.GetDefer("k") != c.GetExplicit("k") {
		t.Fatal("counter differs")
	}
}

func TestWorkerPool(t *testing.T) {
	for _, n := range []int{0, 1, 500} {
		in := ints(n)
		b, startedB := HashAllBaseline(in)
		c, startedC := HashAllCandidate(in, 4)
		if !slices.Equal(b, c) {
			t.Fatalf("n=%d results differ", n)
		}
		if startedB != n || startedC != 4 {
			t.Fatalf("goroutines started %d -> %d", startedB, startedC)
		}
		t.Logf("n=%d goroutines started: %d -> %d", n, startedB, startedC)
	}
}

func TestBatching(t *testing.T) {
	for _, n := range []int{0, 1, 1000} {
		in := ints(n)
		sb, nb := SumViaChannelBaseline(in)
		sc, nc := SumViaChannelCandidate(in, 128)
		if sb != sc {
			t.Fatalf("n=%d sums differ", n)
		}
		if want := (n + 127) / 128; nc != want || nb != n {
			t.Fatalf("sends %d -> %d", nb, nc)
		}
	}
}

func TestChannelBuffering(t *testing.T) {
	for _, n := range []int{0, 1, 1000} {
		in := ints(n)
		if SumUnbuffered(in) != SumBuffered(in, 128) {
			t.Fatalf("n=%d sums differ", n)
		}
	}
}

func TestCounters(t *testing.T) {
	var m MutexCounter
	var a AtomicCounter
	const g, per = 8, 1000
	var done = make(chan struct{})
	for range g {
		go func() {
			for range per {
				m.Inc()
				a.Inc()
			}
			done <- struct{}{}
		}()
	}
	for range g {
		<-done
	}
	if m.Load() != g*per || a.Load() != g*per {
		t.Fatal("lost updates")
	}
}

func TestShardedAggregation(t *testing.T) {
	shards := [][]string{words(300), words(50), nil, words(300)}
	cb, lb := CountWordsBaseline(shards)
	cc, lc := CountWordsCandidate(shards)
	if !maps.Equal(cb, cc) {
		t.Fatal("counts differ")
	}
	if lb != 650 || lc != len(shards) {
		t.Fatalf("lock acquisitions %d -> %d", lb, lc)
	}
}

func TestBufferedWriter(t *testing.T) {
	in := ints(2000)
	var ob, oc bytes.Buffer
	wb, wc := &CountingWriter{W: &ob}, &CountingWriter{W: &oc}
	if WriteLinesBaseline(wb, in) != nil || WriteLinesCandidate(wc, in) != nil {
		t.Fatal("write error")
	}
	if !bytes.Equal(ob.Bytes(), oc.Bytes()) {
		t.Fatal("output differs")
	}
	if wb.Calls != len(in) || wc.Calls > ob.Len()/4096+1 {
		t.Fatalf("write calls %d -> %d", wb.Calls, wc.Calls)
	}
	t.Logf("write calls %d -> %d", wb.Calls, wc.Calls)
}

func TestBufferedReader(t *testing.T) {
	text := lines(abs(ints(2000)))
	for _, s := range []string{"", "7", "1\n2", text} {
		rb := &CountingReader{R: strings.NewReader(s)}
		rc := &CountingReader{R: strings.NewReader(s)}
		b, errB := SumLinesBaseline(rb)
		c, errC := SumLinesCandidate(rc)
		if b != c || errB != nil || errC != nil {
			t.Fatalf("%q: %d %v / %d %v", s[:min(len(s), 10)], b, errB, c, errC)
		}
		if s == text {
			t.Logf("read calls %d -> %d", rb.Calls, rc.Calls)
			if rc.Calls*100 > rb.Calls {
				t.Fatal("bufio did not reduce Read calls")
			}
		}
	}
	long := strings.Repeat("9", 70<<10)
	_, err := SumLinesCandidate(strings.NewReader(long))
	if !errors.Is(err, bufio.ErrTooLong) {
		t.Fatalf("want bufio.ErrTooLong past MaxScanTokenSize, got %v", err)
	}
}

func TestSumUint16Equivalent(t *testing.T) {
	for _, d := range [][]byte{nil, {1}, {1, 2, 3}, []byte("abcdefgh")} {
		b, eb := SumUint16Baseline(d)
		c, ec := SumUint16Candidate(d)
		if b != c || (eb == nil) != (ec == nil) {
			t.Fatalf("%v", d)
		}
	}
	var se *ShortError
	_, err := (&Reader{buf: []byte{1}}).Uint16Candidate()
	if !errors.As(err, &se) || !errors.Is(err, ErrShort) {
		t.Fatal("candidate error must unwrap to ErrShort")
	}
}
