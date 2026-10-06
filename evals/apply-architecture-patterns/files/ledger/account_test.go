package ledger_test

import (
	"testing"

	"example.com/ledger"
)

func TestNewAccountBalance(t *testing.T) {
	if got := ledger.NewAccount("a", 500).Balance(); got != 500 {
		t.Fatalf("Balance() = %d, want 500", got)
	}
}
