package constructs

import (
	"sync"
	"sync/atomic"
)

func hash(v int) int {
	x := uint64(v)
	for range 64 {
		x ^= x << 13
		x ^= x >> 7
		x ^= x << 17
	}
	return int(x >> 1)
}

// --- Bounded worker pool ----------------------------------------------------

// HashAllBaseline starts one goroutine per item. The second result is the
// number of goroutines started.
func HashAllBaseline(items []int) ([]int, int) {
	out := make([]int, len(items))
	var wg sync.WaitGroup
	for i, v := range items {
		wg.Go(func() { out[i] = hash(v) })
	}
	wg.Wait()
	return out, len(items)
}

// HashAllCandidate runs a fixed number of workers over an index channel.
// Results are written by index, so output order matches input order.
func HashAllCandidate(items []int, workers int) ([]int, int) {
	out := make([]int, len(items))
	jobs := make(chan int, workers)
	var wg sync.WaitGroup
	for range workers {
		wg.Go(func() {
			for i := range jobs {
				out[i] = hash(items[i])
			}
		})
	}
	for i := range items {
		jobs <- i
	}
	close(jobs) // workers exit their range loop
	wg.Wait()   // completion means joined, not merely scheduled
	return out, workers
}

// --- Batching channel sends -------------------------------------------------

func SumViaChannelBaseline(items []int) (sum int, sends int) {
	ch := make(chan int, 64)
	go func() {
		for _, v := range items {
			ch <- v
		}
		close(ch)
	}()
	for v := range ch {
		sum += v
		sends++
	}
	return sum, sends
}

func SumViaChannelCandidate(items []int, batch int) (sum int, sends int) {
	ch := make(chan []int, 4)
	go func() {
		for start := 0; start < len(items); start += batch {
			end := min(start+batch, len(items))
			ch <- items[start:end] // read-only view; producer never mutates
		}
		close(ch)
	}()
	for chunk := range ch {
		for _, v := range chunk {
			sum += v
		}
		sends++
	}
	return sum, sends
}

// --- Mutex counter vs atomic counter ---------------------------------------

type MutexCounter struct {
	mu sync.Mutex
	n  int64
}

func (c *MutexCounter) Inc() { c.mu.Lock(); c.n++; c.mu.Unlock() }

func (c *MutexCounter) Load() int64 {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.n
}

type AtomicCounter struct{ n atomic.Int64 }

func (c *AtomicCounter) Inc() { c.n.Add(1) }

func (c *AtomicCounter) Load() int64 { return c.n.Load() }

// --- Per-worker aggregation instead of a shared lock -----------------------

// CountWordsBaseline takes the shared lock once per word.
func CountWordsBaseline(shards [][]string) (map[string]int, int) {
	var mu sync.Mutex
	locks := 0
	counts := make(map[string]int)
	var wg sync.WaitGroup
	for _, shard := range shards {
		wg.Go(func() {
			for _, w := range shard {
				mu.Lock()
				counts[w]++
				locks++
				mu.Unlock()
			}
		})
	}
	wg.Wait()
	return counts, locks
}

// CountWordsCandidate counts into a local map, then merges once per worker.
func CountWordsCandidate(shards [][]string) (map[string]int, int) {
	var mu sync.Mutex
	locks := 0
	counts := make(map[string]int)
	var wg sync.WaitGroup
	for _, shard := range shards {
		wg.Go(func() {
			local := make(map[string]int)
			for _, w := range shard {
				local[w]++
			}
			mu.Lock()
			for w, n := range local {
				counts[w] += n
			}
			locks++
			mu.Unlock()
		})
	}
	wg.Wait()
	return counts, locks
}

// --- Buffered vs unbuffered channel ----------------------------------------

// SumUnbuffered hands each item over synchronously: every send waits for
// the receiver.
func SumUnbuffered(items []int) int { return sumVia(make(chan int), items) }

// SumBuffered lets the producer run up to capacity items ahead.
func SumBuffered(items []int, capacity int) int {
	return sumVia(make(chan int, capacity), items)
}

func sumVia(ch chan int, items []int) int {
	go func() {
		for _, v := range items {
			ch <- v
		}
		close(ch)
	}()
	sum := 0
	for v := range ch {
		sum += v
	}
	return sum
}
