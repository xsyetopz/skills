package constructs

import (
	"bytes"
	"runtime/pprof"
	"strings"
	"testing"
	"time"
)

// leakCount reads the goroutineleak profile (Go 1.27+). The runtime finds
// leaks during GC; WriteTo triggers the detection cycle.
func leakCount(t *testing.T) string {
	t.Helper()
	p := pprof.Lookup("goroutineleak")
	if p == nil {
		t.Skip("goroutineleak profile needs Go 1.27+")
	}
	var buf bytes.Buffer
	if err := p.WriteTo(&buf, 1); err != nil {
		t.Fatal(err)
	}
	first, _, _ := strings.Cut(buf.String(), "\n")
	return first
}

func TestNoLeakedGoroutines(t *testing.T) {
	before := leakCount(t)
	HashAllCandidate(ints(100), 4)
	SumViaChannelCandidate(ints(100), 16)
	if after := leakCount(t); after != before {
		t.Fatalf("leak profile changed: %q -> %q", before, after)
	}
}

func TestLeakProfileDetectsLeak(t *testing.T) {
	before := leakCount(t)
	func() {
		ch := make(chan int)
		go func() { ch <- 1 }() // no receiver ever: blocked forever
	}() // ch is unreachable from here on
	// The goroutine must reach its blocking send before GC can see it.
	after := before
	for i := 0; i < 200 && after == before; i++ {
		time.Sleep(time.Millisecond)
		after = leakCount(t)
	}
	t.Logf("%s -> %s", before, after)
	if after == before {
		t.Fatal("expected the deliberately leaked goroutine to be reported")
	}
}
