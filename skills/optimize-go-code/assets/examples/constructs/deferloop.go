package constructs

import "sync"

// Resource models a file or connection; Open counts live handles.
type Resource struct{ pool *Handles }

type Handles struct {
	Live, Peak int
}

func (h *Handles) Open() *Resource {
	h.Live++
	h.Peak = max(h.Peak, h.Live)
	return &Resource{pool: h}
}

func (r *Resource) Close() { r.pool.Live-- }

// ProcessBaseline defers inside the loop: every Close runs at function
// return, so all handles stay open together and the defers are not
// open-coded.
func ProcessBaseline(h *Handles, n int) int {
	done := 0
	for i := 0; i < n; i++ {
		r := h.Open()
		defer r.Close()
		done++
	}
	return done
}

// ProcessCandidate moves the body into a function so each Close runs at the
// end of its iteration and the single defer is open-coded.
func ProcessCandidate(h *Handles, n int) int {
	done := 0
	for i := 0; i < n; i++ {
		done += processOne(h)
	}
	return done
}

func processOne(h *Handles) int {
	r := h.Open()
	defer r.Close()
	return 1
}

// --- defer in a small hot function -----------------------------------------

type Counter struct {
	mu sync.Mutex
	n  map[string]int
}

func (c *Counter) GetDefer(k string) int {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.n[k]
}

func (c *Counter) GetExplicit(k string) int {
	c.mu.Lock()
	v := c.n[k]
	c.mu.Unlock()
	return v
}
