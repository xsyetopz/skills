package constructs

import (
	"bytes"
	"os"
	"strings"
	"testing"
)

// Sub-benchmarks are named impl=baseline and impl=candidate so one output
// file compares with: benchstat -col /impl bench.txt

var (
	benchInts   []int
	benchStr    string
	benchBytes  []byte
	benchInt    int
	benchU32    uint32
	benchF64    float64
	benchI64    int64
	benchHeader Header
	benchHdrPtr *Header
)

// compare runs baseline and candidate with b.Loop (Go 1.24+). b.Loop
// times only the loop, so setup before compare is excluded.
func compare(b *testing.B, baseline, candidate func()) {
	b.Run("impl=baseline", func(b *testing.B) {
		b.ReportAllocs()
		for b.Loop() {
			baseline()
		}
	})
	b.Run("impl=candidate", func(b *testing.B) {
		b.ReportAllocs()
		for b.Loop() {
			candidate()
		}
	})
}

func BenchmarkPrealloc(b *testing.B) {
	in := ints(1000)
	compare(b,
		func() { benchInts = SquaresBaseline(in) },
		func() { benchInts = SquaresCandidate(in) })
}

func BenchmarkMapHint(b *testing.B) {
	w := words(1000)
	compare(b,
		func() { _ = IndexBaseline(w) },
		func() { _ = IndexCandidate(w) })
}

func BenchmarkBuilder(b *testing.B) {
	w := words(100)
	compare(b,
		func() { benchStr = JoinBaseline(w, ",") },
		func() { benchStr = JoinCandidate(w, ",") })
}

func BenchmarkStrconv(b *testing.B) {
	in := ints(200)
	compare(b,
		func() { benchStr = CSVBaseline(in) },
		func() { benchStr = CSVCandidate(in) })
}

func BenchmarkBufferReuse(b *testing.B) {
	rows := words(100)
	var r Renderer
	compare(b,
		func() { benchBytes = RenderBaseline(rows) },
		func() { benchBytes = r.Render(rows) })
}

func BenchmarkConversion(b *testing.B) {
	keys, m := longKeys(100)
	compare(b,
		func() { benchInt = LookupBaseline(m, keys) },
		func() { benchInt = LookupCandidate(m, keys) })
}

func BenchmarkPoolBuffer(b *testing.B) {
	f := words(20)
	compare(b,
		func() { benchStr = EncodeBaseline(f) },
		func() { benchStr = EncodeCandidate(f) })
}

func BenchmarkPoolPointer(b *testing.B) {
	d := []byte(strings.Repeat("x", 300))
	compare(b,
		func() { benchU32 = ChecksumSlicePool(d) },
		func() { benchU32 = ChecksumPtrPool(d) })
}

func BenchmarkClear(b *testing.B) {
	batches := [][]string{words(200), words(200), words(200)}
	compare(b,
		func() { benchInt = BatchCountsBaseline(batches) },
		func() { benchInt = BatchCountsCandidate(batches) })
}

func BenchmarkStructKey(b *testing.B) {
	const long = "/api/v1/organizations/members/settings"
	mb := BuildRoutesBaseline([]string{"GET"}, []string{long})
	mc := BuildRoutesCandidate([]string{"GET"}, []string{long})
	compare(b,
		func() { benchInt, _ = RouteBaseline(mb, "GET", long) },
		func() { benchInt, _ = RouteCandidate(mc, "GET", long) })
}

func BenchmarkSort(b *testing.B) {
	src := ints(500)
	buf := make([]int, len(src))
	compare(b,
		func() { copy(buf, src); SortBaseline(buf) },
		func() { copy(buf, src); SortCandidate(buf) })
}

func BenchmarkSortedKeys(b *testing.B) {
	_, m := longKeys(500)
	var keys []string
	compare(b,
		func() { keys = SortedKeysBaseline(m) },
		func() { keys = SortedKeysCandidate(m) })
	_ = keys
}

func BenchmarkEscape(b *testing.B) {
	line := "Content-Type: application/json"
	compare(b,
		func() { benchHdrPtr = ParseHeaderBaseline(line) },
		func() { benchHeader, _ = ParseHeaderCandidate(line) })
}

func BenchmarkBCE(b *testing.B) {
	x, y := ints(4096), ints(4096)
	compare(b,
		func() { benchInt = DotBaseline(x, y) },
		func() { benchInt = DotCandidate(x, y) })
}

func BenchmarkInline(b *testing.B) {
	data := bytes.Repeat([]byte{1, 2, 3, 4}, 1024)
	compare(b,
		func() { benchInt, _ = SumUint16Baseline(data) },
		func() { benchInt, _ = SumUint16Candidate(data) })
}

func BenchmarkReceiver(b *testing.B) {
	var s Stats
	for i := range s.Buckets {
		s.Buckets[i] = int64(i)
	}
	compare(b,
		func() { benchI64 = s.TotalValue() },
		func() { benchI64 = s.TotalPointer() })
}

func BenchmarkBoxing(b *testing.B) {
	r := rects(200)
	compare(b,
		func() { benchF64 = AreaBaseline(r) },
		func() { benchF64 = AreaCandidate(r) })
}

func BenchmarkDeferHot(b *testing.B) {
	c := Counter{n: map[string]int{"k": 7}}
	compare(b,
		func() { benchInt = c.GetDefer("k") },
		func() { benchInt = c.GetExplicit("k") })
}

func BenchmarkWorkerPool(b *testing.B) {
	in := ints(2000)
	compare(b,
		func() { benchInts, _ = HashAllBaseline(in) },
		func() { benchInts, _ = HashAllCandidate(in, 8) })
}

func BenchmarkBatching(b *testing.B) {
	in := ints(10000)
	compare(b,
		func() { benchInt, _ = SumViaChannelBaseline(in) },
		func() { benchInt, _ = SumViaChannelCandidate(in, 128) })
}

func BenchmarkChannelBuffer(b *testing.B) {
	in := ints(10000)
	compare(b,
		func() { benchInt = SumUnbuffered(in) },
		func() { benchInt = SumBuffered(in, 128) })
}

func BenchmarkSharded(b *testing.B) {
	shards := [][]string{words(1000), words(1000), words(1000), words(1000)}
	compare(b,
		func() { _, benchInt = CountWordsBaseline(shards) },
		func() { _, benchInt = CountWordsCandidate(shards) })
}

// BenchmarkWriter writes to os.DevNull so every Write is a real syscall;
// io.Discard would make unbuffered writes free and hide the cost.
func BenchmarkWriter(b *testing.B) {
	f, err := os.OpenFile(os.DevNull, os.O_WRONLY, 0)
	if err != nil {
		b.Fatal(err)
	}
	defer f.Close()
	in := ints(2000)
	compare(b,
		func() { _ = WriteLinesBaseline(f, in) },
		func() { _ = WriteLinesCandidate(f, in) })
}

func BenchmarkReader(b *testing.B) {
	text := lines(abs(ints(2000)))
	compare(b,
		func() { benchInt, _ = SumLinesBaseline(strings.NewReader(text)) },
		func() { benchInt, _ = SumLinesCandidate(strings.NewReader(text)) })
}

// Counters use RunParallel: contention is the cost being compared.
func BenchmarkCounter(b *testing.B) {
	b.Run("impl=baseline", func(b *testing.B) {
		var c MutexCounter
		b.RunParallel(func(pb *testing.PB) {
			for pb.Next() {
				c.Inc()
			}
		})
	})
	b.Run("impl=candidate", func(b *testing.B) {
		var c AtomicCounter
		b.RunParallel(func(pb *testing.PB) {
			for pb.Next() {
				c.Inc()
			}
		})
	})
}

// BenchmarkJoinLegacyN is the pre-Go 1.24 shape: setup, ResetTimer, a loop
// to b.N, and a package-level sink so the result is not dead code.
func BenchmarkJoinLegacyN(b *testing.B) {
	w := words(100)
	b.ReportAllocs()
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		benchStr = JoinCandidate(w, ",")
	}
}
