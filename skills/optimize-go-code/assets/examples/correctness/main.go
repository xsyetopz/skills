// Identical expected outcomes for mutant and corrected implementations.
package main
import (
    "fmt"
    "os"
    "sort"
    "strconv"
    "unicode/utf8"
)
func contract(bad bool, topic int) bool {
    switch topic {
    case 1: // Appending through a view must not overwrite another owner.
        owner := make([]int, 1, 2); owner[0] = 1
        snapshot := owner[:1]
        if !bad { snapshot = append([]int(nil), owner...) }
        extended := append(snapshot, 2)
        owner = append(owner, 3)
        return extended[1] == 2
    case 2: // Small retained result must not keep the large backing allocation.
        owner := make([]byte, 1<<20)
        result := owner[:1]
        if !bad { result = append([]byte(nil), result...) }
        return len(result) == 1 && cap(result) < 1<<20
    case 3: // Absent result is a nil interface, not an interface holding a typed nil.
        var p *int
        var result any
        if bad { result = p }
        return result == nil
    case 4: // Sort an admissible arbitrary key order; do not rely on map iteration.
        keys := []int{2, 1}
        if !bad { sort.Ints(keys) }
        return keys[0] == 1 && keys[1] == 2
    case 5: // Count Unicode scalar values, explicitly not grapheme clusters.
        count := len("🙂")
        if !bad { count = utf8.RuneCountInString("🙂") }
        return count == 1
    case 6: // Mutations must reach the authoritative object, not a value copy.
        type counter struct { value int }
        owner := counter{}
        if bad { copy := owner; copy.value++ } else { ref := &owner; ref.value++ }
        return owner.value == 1
    case 7: // A returned byte snapshot must be independent of later owner mutation.
        owner := []byte("ab"); snapshot := owner[:]
        if !bad { snapshot = append([]byte(nil), owner...) }
        owner[0] = 'z'
        return string(snapshot) == "ab"
    case 8: // Completion means joined work, not merely scheduled work.
        release, done := make(chan struct{}), make(chan struct{})
        go func() { <-release; close(done) }()
        finished := false
        if bad {
            select { case <-done: finished = true; default: }
            close(release); <-done // Clean up even the deliberately incorrect path.
        } else { close(release); <-done; finished = true }
        return finished
    default: panic("topic must be 1..8")
    }
}
func main() {
    if len(os.Args) != 3 || (os.Args[1] != "red" && os.Args[1] != "green") {
        fmt.Fprintln(os.Stderr, "usage: red|green TOPIC"); os.Exit(2)
    }
    topic, err := strconv.Atoi(os.Args[2])
    if err != nil || topic < 1 || topic > 8 { fmt.Fprintln(os.Stderr, "topic must be 1..8"); os.Exit(2) }
    pass := contract(os.Args[1] == "red", topic)
    verdict := "FAIL"; if pass { verdict = "PASS" }
    fmt.Printf("CONTRACT topic %d: %s\n", topic, verdict)
    if !pass { os.Exit(1) }
}
