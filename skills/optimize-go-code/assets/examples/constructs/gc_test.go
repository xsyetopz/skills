//go:build !race

package constructs

import (
	"math"
	"testing"
)

// GOGC trades memory for GC CPU: a higher percent means fewer cycles for
// the same allocation stream (https://go.dev/doc/gc-guide).
func TestGOGCReducesCycles(t *testing.T) {
	var low, high uint32
	WithGC(50, math.MaxInt64, func() { low, _ = Churn(8<<20, 200_000) })
	WithGC(400, math.MaxInt64, func() { high, _ = Churn(8<<20, 200_000) })
	t.Logf("GC cycles GOGC=50: %d, GOGC=400: %d", low, high)
	if high >= low {
		t.Fatalf("GOGC=400 ran %d cycles, GOGC=50 ran %d", high, low)
	}
}

// With GOGC=off the heap grows without collecting until the soft memory
// limit forces cycles.
func TestMemoryLimitForcesCycles(t *testing.T) {
	var off, limited uint32
	WithGC(-1, math.MaxInt64, func() { off, _ = Churn(8<<20, 100_000) })
	WithGC(-1, 32<<20, func() { limited, _ = Churn(8<<20, 100_000) })
	t.Logf("GC cycles GOGC=off: %d, GOGC=off+limit 32 MiB: %d", off, limited)
	if off != 0 || limited == 0 {
		t.Fatalf("off=%d limited=%d", off, limited)
	}
}
