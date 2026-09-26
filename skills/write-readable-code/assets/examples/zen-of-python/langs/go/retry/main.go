// Complex is better than complicated: the retry policy lives in one
// function with one test, not as sleep-and-retry loops at each call site.
package main

import (
	"context"
	"errors"
	"fmt"
	"os"
	"time"
)

var errTransient = errors.New("transient")

// Retry calls op until it succeeds, returns a non-transient error, runs
// out of delays, or ctx ends. It waits delays[i] after failure i.
func Retry(ctx context.Context, delays []time.Duration, op func() error) error {
	for attempt := 0; ; attempt++ {
		err := op()
		done := err == nil || !errors.Is(err, errTransient)
		if done || attempt == len(delays) {
			return err
		}
		select {
		case <-ctx.Done():
			return errors.Join(err, ctx.Err())
		case <-time.After(delays[attempt]):
		}
	}
}

func check(ok bool, message string) {
	if !ok {
		fmt.Println("FAIL", message)
		os.Exit(1)
	}
}

func main() {
	ctx := context.Background()
	delays := []time.Duration{time.Millisecond, 2 * time.Millisecond}

	calls := 0
	err := Retry(ctx, delays, func() error {
		calls++
		if calls < 3 {
			return fmt.Errorf("attempt %d: %w", calls, errTransient)
		}
		return nil
	})
	check(err == nil && calls == 3, "succeeds on third attempt")

	calls = 0
	err = Retry(ctx, delays, func() error { calls++; return errTransient })
	check(errors.Is(err, errTransient) && calls == 3, "gives up after delays")

	calls = 0
	permanent := errors.New("permanent")
	err = Retry(ctx, delays, func() error { calls++; return permanent })
	check(errors.Is(err, permanent) && calls == 1, "does not retry permanent")

	cancelled, cancel := context.WithCancel(ctx)
	cancel()
	err = Retry(cancelled, delays, func() error { return errTransient })
	check(errors.Is(err, context.Canceled), "stops on cancel")
	fmt.Println("retry: 4 policy cases pass")
}
