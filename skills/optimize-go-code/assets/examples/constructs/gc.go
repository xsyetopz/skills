package constructs

import (
	"runtime"
	"runtime/debug"
)

// Churn allocates n short-lived 1 KiB buffers while keeping live bytes of
// long-lived data reachable, and returns the number of GC cycles it caused.
func Churn(live, n int) (cycles uint32, checksum int) {
	retained := make([][]byte, live/1024)
	for i := range retained {
		retained[i] = make([]byte, 1024)
	}
	var before, after runtime.MemStats
	runtime.ReadMemStats(&before)
	for i := range n {
		b := make([]byte, 1024)
		b[i%1024] = byte(i)
		checksum += int(b[i%1024])
		sinkBytes = b
	}
	runtime.ReadMemStats(&after)
	runtime.KeepAlive(retained)
	return after.NumGC - before.NumGC, checksum
}

var sinkBytes []byte

// WithGC runs f with GOGC and the memory limit set, then restores both.
func WithGC(percent int, limit int64, f func()) {
	oldPercent := debug.SetGCPercent(percent)
	oldLimit := debug.SetMemoryLimit(limit)
	defer func() {
		debug.SetGCPercent(oldPercent)
		debug.SetMemoryLimit(oldLimit)
	}()
	runtime.GC()
	f()
}
