// Command pgodemo is a PGO target: it writes a CPU profile of its own
// workload with -cpuprofile, which verify.sh installs as default.pgo.
package main

import (
	"flag"
	"fmt"
	"os"
	"runtime/pprof"
	"strings"
)

// Tokenizer is an interface so the hot call is an indirect call that PGO
// can devirtualize and inline.
type Tokenizer interface {
	Next(s string, i int) (string, int)
}

type fieldTokenizer struct{ sep byte }

func (t fieldTokenizer) Next(s string, i int) (string, int) {
	j := strings.IndexByte(s[i:], t.sep)
	if j < 0 {
		return s[i:], len(s)
	}
	return s[i : i+j], i + j + 1
}

func count(tok Tokenizer, s string) int {
	n := 0
	for i := 0; i < len(s); {
		var field string
		field, i = tok.Next(s, i)
		n += len(field)
	}
	return n
}

func main() {
	profile := flag.String("cpuprofile", "", "write a CPU profile here")
	rounds := flag.Int("rounds", 400000, "workload repetitions")
	flag.Parse()
	if *profile != "" {
		f, err := os.Create(*profile)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		defer f.Close()
		if err := pprof.StartCPUProfile(f); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		defer pprof.StopCPUProfile()
	}
	line := strings.Repeat("alpha,beta,gamma,delta,", 64)
	var tok Tokenizer = fieldTokenizer{sep: ','}
	total := 0
	for range *rounds {
		total += count(tok, line)
	}
	fmt.Println(total)
}
