package constructs

// DotCandidate checks the length once, so the compiler proves every b[i]
// in range. Do not write b = b[:len(a)] instead: reslicing up to cap(b)
// succeeds and silently reads elements past len(b).
func DotCandidate(a, b []int) int {
	if len(b) < len(a) {
		panic("DotCandidate: len(b) < len(a)")
	}
	sum := 0
	for i := range a {
		sum += a[i] * b[i]
	}
	return sum
}
