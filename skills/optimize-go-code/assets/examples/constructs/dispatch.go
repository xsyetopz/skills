package constructs

// --- Pointer vs value receivers -------------------------------------------

// Stats is large: a value receiver copies all 520 bytes per call.
type Stats struct {
	Buckets [64]int64
	Count   int64
}

func (s Stats) TotalValue() int64 {
	var t int64
	for _, b := range s.Buckets {
		t += b
	}
	return t + s.Count
}

func (s *Stats) TotalPointer() int64 {
	var t int64
	for _, b := range s.Buckets {
		t += b
	}
	return t + s.Count
}

// AddValue shows the semantic trap: the increment is applied to a copy.
func (s Stats) AddValue(bucket int) { s.Buckets[bucket]++; s.Count++ }

func (s *Stats) AddPointer(bucket int) { s.Buckets[bucket]++; s.Count++ }

// --- Interface boxing vs concrete/generic slices ---------------------------

type Shape interface{ Area() float64 }

type Rect struct{ W, H float64 }

func (r Rect) Area() float64 { return r.W * r.H }

// AreaBaseline converts every Rect to Shape, heap-allocating each one.
func AreaBaseline(rects []Rect) float64 {
	shapes := make([]Shape, 0, len(rects))
	for _, r := range rects {
		shapes = append(shapes, r)
	}
	total := 0.0
	for _, s := range shapes {
		total += s.Area()
	}
	return total
}

// Areas is generic over the concrete element type: no boxing.
type Areas[S Shape] []S

func (a Areas[S]) Total() float64 {
	total := 0.0
	for _, s := range a {
		total += s.Area()
	}
	return total
}

// AreaCandidate keeps []Rect concrete and sums through Areas.
func AreaCandidate(rects []Rect) float64 { return Areas[Rect](rects).Total() }

// --- Struct field order and padding ----------------------------------------

type EventPadded struct {
	Active  bool
	ID      int64
	Retries uint8
	Offset  int32
	Urgent  bool
}

type EventPacked struct {
	ID      int64
	Offset  int32
	Retries uint8
	Active  bool
	Urgent  bool
}
