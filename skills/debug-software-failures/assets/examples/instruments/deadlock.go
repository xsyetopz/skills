// A send on an unbuffered channel with no receiver blocks forever; the Go
// runtime detects that every goroutine is blocked and prints their stacks.
package main

import "fmt"

func main() {
	results := make(chan int)
	results <- 42 // no goroutine ever receives
	fmt.Println(<-results)
}
